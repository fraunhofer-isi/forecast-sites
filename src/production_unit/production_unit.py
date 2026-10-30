# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from carrier.carrier_unit import CarrierUnit
from interpolation.interpolator import interpolate
from optimization.multi_period_optimization_result import MultiPeriodOptimizationResult
from optimization.optimization_result import OptimizationResult
from processes.installed_process import InstalledProcess
from processes.process_option import ProcessOption
from production_unit.carrier_export_calculator import CarrierExportCalculator
from result.visitor.entity import Entity


# pylint: disable=too-many-instance-attributes
class ProductionUnit(Entity):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        id_production_unit,
        site,
        sector,
        minimum_export_interpolation_data_in_t,
        sub_production_unit_factory,
        optimization_factory,
        process_map,
        carriers,
        simulation_options,
    ):
        super().__init__(id_production_unit)

        self._site = site
        self.sector = sector
        self._minimum_export_interpolation_data_in_t = minimum_export_interpolation_data_in_t
        self._sub_production_unit_factory = sub_production_unit_factory
        self._optimization_factory = optimization_factory

        self._original_processes = list(process_map.values())

        self.available_carriers = carriers

        self.sub_production_units = self._sub_production_unit_factory.create_for_start_year(id_production_unit)

        self._sub_production_unit_inactivity = self._initialize_sub_production_inactivity()
        self._process_option_mapping = self._process_option_to_sub_production_unit_mapping()

        self.optimization_results = self._extract_pseudo_optimization_results_for_start_year(simulation_options)
        self._multi_period_result = None

    @property
    def available_process_options(self):
        processes_options = list(self._process_option_mapping.keys())
        return processes_options

    @property
    def purchased_carrier_amounts(self):
        return self.optimization_results.purchased_carrier_amounts

    @property
    def used_carriers(self):
        carrier_set = set()
        for sub_production_unit in self.sub_production_units:
            sub_carriers = sub_production_unit.used_carriers
            carrier_set.update(sub_carriers)
        carriers = list(carrier_set)
        return carriers

    @property
    def products(self):
        products = list(self._minimum_export_interpolation_data_in_t.keys())
        return products

    @property
    def by_products(self):
        by_products_set = set()
        for sub_production_unit in self.sub_production_units:
            sub_by_products = sub_production_unit.output_by_products
            by_products_set.update(sub_by_products)
        by_products = list(by_products_set)
        return by_products

    @property
    def used_process_ids(self):
        unique_process_ids = set()
        for sub_production_unit in self.sub_production_units:
            process_id = sub_production_unit.id_process
            unique_process_ids.add(process_id)
        process_ids = list(unique_process_ids)
        return process_ids

    @property
    def multi_period_budget_summary(self):
        if self._multi_period_result is None:
            return None
        return self._multi_period_result.overall_emission_budget_summary

    @property
    def _reverse_process_option_mapping(self):
        reverse_mapping = {
            sub_production_unit: process_option
            for process_option, sub_production_unit in self._process_option_mapping.items()
            if sub_production_unit is not None
        }
        return reverse_mapping

    def _has_cached_multi_period_result(self, year):
        return self._multi_period_result is not None and self._multi_period_result.has_result_for_year(year)

    def optimize(self, year, context):
        if self._has_cached_multi_period_result(year):
            cached_result = self._multi_period_result
            if cached_result is None:
                message = 'Expected cached multi-period result to be available.'
                raise RuntimeError(message)
            self.optimization_results = cached_result.get_result_for_year(year)
            self._apply_multi_period_results(year, context)
            return

        self._remove_inactive_sub_production_units(year)
        self._process_option_mapping = self._process_option_to_sub_production_unit_mapping()
        optimization = self._optimization_factory.create(
            year,
            self,
            context,
        )
        optimization_result = optimization.optimize()

        if isinstance(optimization_result, MultiPeriodOptimizationResult):
            self._multi_period_result = optimization_result
            self.optimization_results = optimization_result.get_result_for_year(year)
            self._apply_multi_period_results(year, context)
            return

        self.optimization_results = optimization_result
        self._apply_results(year, context)

    def accept(self, visitor, year):
        enter_results = visitor.enter_production_unit(self, year)

        child_results = {}
        for sub_production_unit in self.sub_production_units:
            child_result = sub_production_unit.accept(visitor, year)
            child_results[sub_production_unit] = child_result

        result = visitor.exit_production_unit(
            self,
            year,
            enter_results,
            child_results,
        )
        return result

    def consume_purchased_carrier_amounts(self, year, context):
        for carrier, purchased_carrier_amount in self.purchased_carrier_amounts.items():
            if purchased_carrier_amount == 0:
                continue

            self._consume_purchased_carrier_amount(
                carrier,
                purchased_carrier_amount,
                year,
                context,
            )

    def export_produced_carrier_amounts(self, year):
        # Export amounts are calculated for reporting/selling purposes.
        # Pool availability is NOT replenished by production - only purchases count against shared pools.
        for carrier in self.used_carriers:
            export_amount = self._export_amount_for_carrier(year, carrier)
            if export_amount == 0:
                continue
            # Export is recorded for reporting but does not mutate pool availability

    def sell_gain_in_euro(self, year):
        sell_gain_dict = {}
        for carrier in self.used_carriers:
            sell_gain_in_euro = self._sell_gain_in_euro_for_carrier(year, carrier)
            sell_gain_dict[carrier] = sell_gain_in_euro
        return sell_gain_dict

    def export(self, year):
        export_dict = {}
        for carrier in self.used_carriers:
            export_for_carrier = self._export_amount_for_carrier(year, carrier)
            export_dict[carrier] = export_for_carrier
        return export_dict

    def new_investment_in_euro(self, year, simulation_options):
        new_investment = sum(
            sub_production_unit.new_investment_in_euro(year, simulation_options)
            for sub_production_unit in self.sub_production_units
        )
        return new_investment

    def pipeline_cost_in_euro(self):
        cost_scaling_factor = self.pipeline_cost_scaling_factor()
        cost_in_euro = sum(
            sub_production_unit.pipeline_cost_in_euro(cost_scaling_factor) for sub_production_unit in self.sub_production_units
        )
        return cost_in_euro

    def pipeline_cost_scaling_factor(self):
        pipeline_context = self._site.pipeline_context
        scaling = pipeline_context['pipeline_cost_scaling_factor']
        return scaling

    def carrier_purchase_cost_in_euro(self, year):
        purchased_carrier_amounts = self.purchased_carrier_amounts
        purchase_cost = {
            carrier: carrier.purchase_cost_in_euro(amount, year) for carrier, amount in purchased_carrier_amounts.items()
        }
        return purchase_cost

    def energy_carrier_taxes_in_euro(self, year, simulation_options):
        purchased_carrier_amounts = self.purchased_carrier_amounts
        return {
            carrier: carrier.taxes_in_euro_per_unit(year, simulation_options) * amount
            for carrier, amount in purchased_carrier_amounts.items()
            if carrier.unit is CarrierUnit.GJ
        }

    def energy_carrier_subsidies_in_euro(self, year, simulation_options):
        purchased_carrier_amounts = self.purchased_carrier_amounts
        return {
            carrier: carrier.subsidies_in_euro_per_unit(year, simulation_options) * amount
            for carrier, amount in purchased_carrier_amounts.items()
            if carrier.unit is CarrierUnit.GJ
        }

    def carrier_availability(self, carrier, year):
        availability = self._site.carrier_availability(carrier, year)
        return availability

    def carrier_minimum_export_in_t(self, carrier, year, simulation_options):
        if carrier in self._minimum_export_interpolation_data_in_t:
            interpolation_data = self._minimum_export_interpolation_data_in_t[carrier]

            minimum_export = interpolate(year, simulation_options, interpolation_data)
        else:
            minimum_export = 0
        return minimum_export

    def upstream_emission_in_t_co2(self, year, simulation_options):
        # In our model,
        # a) upstream emissions are considered on the level of production units,
        # taking the purchased amounts from the optimization. This already includes
        # the influence of the sub production units and their processes.
        #
        # b) for upstream emissions, we only consider purchased carriers,
        # no business trips, employee commuting, etc.

        purchased_carrier_amounts = self.purchased_carrier_amounts

        upstream_emissions = {}
        for carrier, amount in purchased_carrier_amounts.items():
            upstream_emission_per_unit = carrier.upstream_emission_in_t_co2_per_unit(year, simulation_options)
            emission_in_t_co2 = amount * upstream_emission_per_unit
            upstream_emissions[carrier] = emission_in_t_co2
        return upstream_emissions

    def downstream_emission_in_t_co2(self, year, simulation_options):
        export = self.export(year)
        downstream_emissions = {}
        for carrier, export_amount in export.items():
            if not hasattr(carrier, 'downstream_emission_in_t_co2_per_unit'):
                continue

            # Handle small negative values due to numerical precision
            normalized_export = CarrierExportCalculator.normalize_export_amount(export_amount, carrier)

            if normalized_export == 0:
                continue

            downstream_emission_per_unit = carrier.downstream_emission_in_t_co2_per_unit(year, simulation_options)
            downstream_emissions[carrier] = normalized_export * downstream_emission_per_unit
        return downstream_emissions

    def renewably_bound_co2_emission_in_t_co2(self, year, simulation_options):
        purchased_carrier_amounts = self.purchased_carrier_amounts

        renewably_bound_emissions = {}
        for carrier, amount in purchased_carrier_amounts.items():
            renewably_bound_emission_per_unit = carrier.renewably_bound_co2_emission_in_t_co2_per_unit(year, simulation_options)
            emission_in_t_co2 = amount * renewably_bound_emission_per_unit
            renewably_bound_emissions[carrier] = emission_in_t_co2
        return renewably_bound_emissions

    def budget_relevant_emission_in_t_co2(self, year, simulation_options):
        # Keep emission component composition in sync with LinearProgrammingOptimization
        # and MultiPeriodOptimization.
        scope = simulation_options['emission_constraint_scope']
        total_emissions = 0.0

        if 'direct' in scope:
            direct_emissions = sum(
                sub_production_unit.direct_emissions_in_t_co2(year) for sub_production_unit in self.sub_production_units
            )
            captured_emissions = sum(
                sub_production_unit.installed_process.emission.captured_emission_in_t_co2(
                    sub_production_unit.process_execution_count
                )
                for sub_production_unit in self.sub_production_units
            )
            total_emissions += direct_emissions - captured_emissions

        if 'upstream' in scope:
            total_emissions += sum(self.upstream_emission_in_t_co2(year, simulation_options).values())

        if 'renewably_bound' in scope:
            total_emissions -= sum(self.renewably_bound_co2_emission_in_t_co2(year, simulation_options).values())

        if 'downstream' in scope:
            total_emissions += sum(self.downstream_emission_in_t_co2(year, simulation_options).values())

        return total_emissions

    def number_of_process_usages(self, process):
        number_of_usages = sum(
            sub_production_unit.number_of_process_usages(process) for sub_production_unit in self.sub_production_units
        )
        return number_of_usages

    def _sell_gain_in_euro_for_carrier(self, year, carrier):
        export = self._export_amount_for_carrier(year, carrier)  # in t or GJ
        sell_price = carrier.sell_price_in_euro_per_unit(year)  # in euro per t or euro per GJ
        sell_gain_in_euro = export * sell_price
        return sell_gain_in_euro

    def _export_amount_for_carrier(self, year, carrier):
        purchased_amount = self.purchased_carrier_amounts[carrier]

        # Prefer LP-consistent netto amounts stored in the optimization result.
        # These are computed directly from LP exec values so that
        #   export = purchased_LP + netto_LP  # noqa: ERA001
        # matches the LP constraint, preventing mismatch from vintage reconstruction.
        # Fall back to sub-production-unit reconstruction for start-year pseudo results
        # and any path that does not store carrier_netto_amounts.
        optimized_netto = self.optimization_results.carrier_netto_amounts
        if optimized_netto:
            netto_amount = optimized_netto.get(carrier, 0.0)
        else:
            netto_amount = self._netto_produced_or_consumed_amount_for_carrier_from_sub_production_units(year, carrier)

        # sign is positive here, when determining the export from the optimization results
        export = purchased_amount + netto_amount
        return CarrierExportCalculator.normalize_export_amount(export, carrier)

    def _extract_pseudo_optimization_results_for_start_year(self, simulation_options):
        # We do not run an optimization for the start year, but we put the
        # data of the start year in the same format as an optimization result.
        # This is done to be able to handle the start year similar to the other
        # years regarding the result analysis.
        process_execution_counts = self._extract_process_execution_counts_for_start_year()
        purchased_carrier_amounts = self._determine_purchased_carrier_amounts_for_start_year(simulation_options)

        pseudo_optimization_results = OptimizationResult(
            process_execution_counts,
            purchased_carrier_amounts,
        )

        return pseudo_optimization_results

    def _determine_purchased_carrier_amounts_for_start_year(self, simulation_options):
        start_year = simulation_options['start_year']

        # 0. Initialize with zero for all carriers (energy carriers, products, by-products)
        purchased_amounts = dict.fromkeys(self.available_carriers, 0.0)

        # 1. For the special case of products, we adapt the initial value to the minimum export.
        # Reasoning: if a production unit does not produce anything itself, it has to
        # purchase the required product amounts to fulfill the required minimum export amounts
        # on the level of the production_unit.
        # These initial values will be reduced if products are produced within the production unit, see below.
        # The initial values might also be increased,
        # if a sub_production_unit consumes more of a product than it produces.
        for product, interpolation_data in self._minimum_export_interpolation_data_in_t.items():
            value = interpolation_data.value_for_start_year
            purchased_amounts[product] += value

        # 2. If a carrier is produced by the sub_production_units of this production_unit,
        # the initial value for the purchased amount is reduced by the netto outcome
        # (=export) of the sub_production_unit.
        # However, the purchased amount can never be negative.
        #
        # If the export of a sub_production_unit is negative for a carrier (meaning sub_input > sub_output),
        # the purchased amount for that carrier is increased accordingly.

        for carrier in purchased_amounts:
            sub_production_netto_amount_for_carrier = (
                self._netto_produced_or_consumed_amount_for_carrier_from_sub_production_units(start_year, carrier)
            )
            # Sign convention: netto_amount is positive when produced (export), negative when consumed (import).
            # Here we subtract it: purchased -= netto, which increases purchase if sub_production consumes (netto < 0).
            purchased_amounts[carrier] -= sub_production_netto_amount_for_carrier
            purchased_amounts[carrier] = max(0.0, purchased_amounts[carrier])

        return purchased_amounts

    def _netto_produced_or_consumed_amount_for_carrier_from_sub_production_units(self, year, carrier):
        sub_exports = sum(
            sub_production_unit.netto_produced_or_consumed_amount_for_carrier(year, carrier)
            for sub_production_unit in self.sub_production_units
        )
        return sub_exports

    def _extract_process_execution_counts_for_start_year(self):
        process_execution_counts = dict.fromkeys(self.available_process_options, 0)
        process_execution_counts = self._extract_process_execution_counts_from_existing_sub_production_units(
            process_execution_counts
        )
        return process_execution_counts

    def _extract_process_execution_counts_from_existing_sub_production_units(self, process_execution_counts):
        reverse_process_option_mapping = self._reverse_process_option_mapping

        for sub_production_unit in self.sub_production_units:
            process_option = reverse_process_option_mapping[sub_production_unit]
            process_execution_count = sub_production_unit.process_execution_count
            process_execution_counts[process_option] = process_execution_count
        return process_execution_counts

    def _initialize_sub_production_inactivity(self):
        sub_production_inactivity = {}
        for sub_production_unit in self.sub_production_units:
            execution_count = sub_production_unit.process_execution_count
            if execution_count > 0:
                sub_production_inactivity[sub_production_unit] = 0
            else:
                sub_production_inactivity[sub_production_unit] = 1
        return sub_production_inactivity

    @staticmethod
    def _is_future_planned_sub_production_unit(sub_production_unit, year):
        return sub_production_unit.year_of_last_reinvestment > year

    def _remove_inactive_sub_production_units(self, year):
        max_duration_without_usage = 4
        items_to_delete = [
            sub_production_unit
            for sub_production_unit, duration in self._sub_production_unit_inactivity.items()
            if duration > max_duration_without_usage
            and not self._is_future_planned_sub_production_unit(sub_production_unit, year)
        ]

        for sub_production_unit in items_to_delete:
            del self._sub_production_unit_inactivity[sub_production_unit]
            self.sub_production_units.remove(sub_production_unit)

    def _process_option_to_sub_production_unit_mapping(self):
        # When creating an optimization model from and existing production unit,
        # we have to consider two types of options for processes:
        # 1. The option to reuse InstalledProcesses (=Processes that are already installed in sub production units).
        # 2. The option to use Processes that are not yet installed: new sub production units will be created
        #    if the optimization decides to use those options.

        # a) Initialize mapping with options for original processes
        # If these options are chosen, it means fresh instances of SubProductionUnit and
        # InstalledProcess will be created.
        process_option_mapping = {ProcessOption(process): None for process in self._original_processes}

        # b) Add options for installed processes to the mapping
        # If these options are chosen, it means already existing InstalledProcesses will be reused.

        for sub_production_unit in self.sub_production_units:
            installed_process = sub_production_unit.installed_process
            installed_process_option = ProcessOption(installed_process)
            process_option_mapping[installed_process_option] = sub_production_unit
        return process_option_mapping

    def _apply_results(self, year, context):
        self._create_or_update_sub_production_units(year)
        self.consume_purchased_carrier_amounts(year, context)
        self.export_produced_carrier_amounts(year)

    def _apply_multi_period_results(self, year, context):
        self._create_or_update_sub_production_units_from_multi_period(year)
        self.consume_purchased_carrier_amounts(year, context)
        self.export_produced_carrier_amounts(year)

    def _consume_purchased_carrier_amount(self, carrier, amount, year, context):
        self._site.consume_purchased_carrier_amount(carrier, amount, year, context)

    def _create_or_update_sub_production_units(self, year):
        process_execution_counts = self.optimization_results.process_execution_counts
        for process_option, process_execution_count in process_execution_counts.items():
            sub_production_unit = self._process_option_mapping[process_option]
            if sub_production_unit is None:
                process_is_used = process_execution_count > 0
                if process_is_used:
                    sub_production_unit = self._sub_production_unit_factory.create_sub_production_unit_for_process_option(
                        process_option,
                        process_execution_count,
                        self,
                        year,
                    )
                    self.sub_production_units.append(sub_production_unit)
                    self._sub_production_unit_inactivity[sub_production_unit] = 0
            else:
                sub_production_unit.process_execution_count = process_execution_count
                process_is_used = process_execution_count > 0
                if process_is_used:
                    self._sub_production_unit_inactivity[sub_production_unit] = 0
                elif not self._is_future_planned_sub_production_unit(sub_production_unit, year):
                    self._sub_production_unit_inactivity[sub_production_unit] += 1

    def _create_or_update_sub_production_units_from_multi_period(self, year):
        process_execution_counts = self.optimization_results.process_execution_counts
        multi_period_result = self._multi_period_result
        if multi_period_result is None:
            message = 'Expected cached multi-period result to be available.'
            raise RuntimeError(message)
        new_capacity_counts = multi_period_result.get_new_capacity_for_year(year)

        installed_process_options = [
            process_option for process_option in process_execution_counts if isinstance(process_option.process, InstalledProcess)
        ]

        for process_option in installed_process_options:
            installed_process = process_option.process
            sub_production_unit = self._find_sub_production_unit_for_installed_process(installed_process)
            if sub_production_unit is None:
                continue

            process_execution_count = process_execution_counts[process_option]
            sub_production_unit.process_execution_count = process_execution_count
            if process_execution_count > 0:
                self._sub_production_unit_inactivity[sub_production_unit] = 0
            elif not self._is_future_planned_sub_production_unit(sub_production_unit, year):
                self._sub_production_unit_inactivity[sub_production_unit] = (
                    self._sub_production_unit_inactivity.get(sub_production_unit, 0) + 1
                )

        template_process_options = [
            process_option
            for process_option in process_execution_counts
            if not isinstance(process_option.process, InstalledProcess)
        ]

        for process_option in template_process_options:
            new_capacity = new_capacity_counts.get(process_option, 0)
            if new_capacity <= 0:
                continue

            sub_production_unit = self._sub_production_unit_factory.create_sub_production_unit_for_process_option(
                process_option,
                new_capacity,
                self,
                year,
            )
            sub_production_unit.process_execution_count = 0
            sub_production_unit._is_multi_period_vintage = True
            self.sub_production_units.append(sub_production_unit)
            self._sub_production_unit_inactivity[sub_production_unit] = 0

        for process_option in template_process_options:
            process = process_option.process
            total_execution_count = process_execution_counts[process_option]
            vintages = [
                sub_production_unit
                for sub_production_unit in self.sub_production_units
                if sub_production_unit.installed_process.id == process.id
                and getattr(sub_production_unit, '_is_multi_period_vintage', False)
            ]
            if not vintages:
                continue
            self._split_execution_across_vintages(vintages, total_execution_count, year)

    def _find_sub_production_unit_for_installed_process(self, installed_process):
        for sub_production_unit in self.sub_production_units:
            if sub_production_unit.installed_process is installed_process:
                return sub_production_unit
        return None

    def _split_execution_across_vintages(self, vintages, total_execution_count, year):
        total_capacity = sum(sub_production_unit.max_process_execution_count for sub_production_unit in vintages)

        if total_capacity <= 0:
            for sub_production_unit in vintages:
                sub_production_unit.process_execution_count = 0
            return

        remaining_execution_count = total_execution_count
        for index, sub_production_unit in enumerate(vintages):
            if index == len(vintages) - 1:
                execution_count = max(0.0, remaining_execution_count)
            else:
                execution_count = total_execution_count * sub_production_unit.max_process_execution_count / total_capacity
                execution_count = min(execution_count, sub_production_unit.max_process_execution_count)
                remaining_execution_count -= execution_count

            sub_production_unit.process_execution_count = execution_count
            if execution_count > 0:
                self._sub_production_unit_inactivity[sub_production_unit] = 0
            elif not self._is_future_planned_sub_production_unit(sub_production_unit, year):
                self._sub_production_unit_inactivity[sub_production_unit] = (
                    self._sub_production_unit_inactivity.get(sub_production_unit, 0) + 1
                )
