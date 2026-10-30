# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from by_product.by_product import ByProduct
from carrier.carrier_unit import CarrierUnit
from energy_carrier.energy_carrier import EnergyCarrier
from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand
from product.product import Product
from result import aggregation, result_table_schema
from result.visitor.tabular_visitor import TabularVisitor

# Carrier results whose table name carries the carrier unit as a suffix, for example
# 'purchased_amount_in_gj' versus 'purchased_amount_in_t'.
CARRIER_RESULT_NAMES_WITH_UNIT_SUFFIX = frozenset({'purchased_amount', 'export'})


class CollectingResultVisitor(TabularVisitor):
    def __init__(self, simulation_options):
        super().__init__(simulation_options)

        self._co2_cost_in_euro_per_t_co2 = None
        self._interest_rate = None

    def _initialize(self):
        self._initialize_tables(self._absolute_results, result_table_schema.ABSOLUTE_RESULT_TABLES)
        self._initialize_tables(self._specific_results, result_table_schema.SPECIFIC_RESULT_TABLES)

    def enter_region(self, region, year):
        super().enter_region(region, year)
        self._co2_cost_in_euro_per_t_co2 = region.co2_cost_in_euro_per_t_co2(year)
        self._interest_rate = region.interest_rate

    def exit_site(
        self,
        _site,
        _year,
        _enter_results,
        production_unit_results,
    ):
        results = aggregation.aggregate_dictionaries(production_unit_results)
        purchased_carrier_amounts = results['purchased_carrier_amounts']
        self._handle_site_purchased_carrier_amounts(purchased_carrier_amounts, _year)
        return results

    def exit_production_unit(
        self,
        production_unit,
        year,
        _enter_results,
        sub_production_unit_results,
    ):
        self._collect_production_unit_overall_emission_budget(year, production_unit)
        self._collect_production_unit_budget_relevant_emission(year, production_unit)

        results = aggregation.aggregate_dictionaries(sub_production_unit_results)
        results['purchased_carrier_amounts'] = production_unit.purchased_carrier_amounts

        for result_name, amounts_by_carrier in self._production_unit_carrier_results(production_unit, year):
            self._handle_production_unit_carrier_result(
                amounts_by_carrier,
                result_name,
                year,
                append_unit=result_name in CARRIER_RESULT_NAMES_WITH_UNIT_SUFFIX,
            )

        return results

    def _production_unit_carrier_results(self, production_unit, year):
        """
        Return one (result_name, amounts_by_carrier) pair per carrier result of a production unit.

        The order is the order in which the results are recorded. The three emission cost entries
        are derived from the emission amounts declared above them, so those are computed once here
        and reused instead of being queried twice.
        """
        simulation_options = self._simulation_options
        upstream_emission_in_t_co2 = production_unit.upstream_emission_in_t_co2(year, simulation_options)
        downstream_emission_in_t_co2 = production_unit.downstream_emission_in_t_co2(year, simulation_options)
        renewably_bound_co2_emission_in_t_co2 = production_unit.renewably_bound_co2_emission_in_t_co2(
            year,
            simulation_options,
        )

        return (
            ('purchased_amount', production_unit.purchased_carrier_amounts),
            ('purchase_cost_in_euro', production_unit.carrier_purchase_cost_in_euro(year)),
            ('taxes_in_euro', production_unit.energy_carrier_taxes_in_euro(year, simulation_options)),
            ('subsidies_in_euro', production_unit.energy_carrier_subsidies_in_euro(year, simulation_options)),
            ('export', production_unit.export(year)),
            ('sell_gain_in_euro', production_unit.sell_gain_in_euro(year)),
            ('upstream_emission_in_t_co2', upstream_emission_in_t_co2),
            ('downstream_emission_in_t_co2', downstream_emission_in_t_co2),
            ('renewably_bound_co2_emission_in_t_co2', renewably_bound_co2_emission_in_t_co2),
            ('upstream_emission_cost_in_euro', self._carrier_emission_cost_in_euro(upstream_emission_in_t_co2)),
            ('downstream_emission_cost_in_euro', self._carrier_emission_cost_in_euro(downstream_emission_in_t_co2)),
            (
                'renewably_bound_co2_emission_cost_in_euro',
                self._carrier_emission_cost_in_euro(renewably_bound_co2_emission_in_t_co2, sign=-1),
            ),
        )

    def _collect_production_unit_overall_emission_budget(self, year, production_unit):
        budget_summary = production_unit.multi_period_budget_summary
        if budget_summary is None:
            return

        start_year = self._simulation_options['start_year']
        if year != start_year:
            return

        self._add_production_unit_entry(
            self._absolute_results['production_unit_overall_emission_budget_used_in_t_co2'],
            year,
            budget_summary['used_in_t_co2'],
        )
        self._add_production_unit_entry(
            self._absolute_results['production_unit_overall_emission_budget_in_t_co2'],
            year,
            budget_summary['available_in_t_co2'],
        )

    def _collect_production_unit_budget_relevant_emission(self, year, production_unit):
        budget_relevant_emission_in_t_co2 = production_unit.budget_relevant_emission_in_t_co2(
            year,
            self._simulation_options,
        )
        self._add_production_unit_entry(
            self._absolute_results['production_unit_budget_relevant_emission_in_t_co2'],
            year,
            budget_relevant_emission_in_t_co2,
        )

    def exit_sub_production_unit(
        self,
        sub_production_unit,
        year,
        _enter_results,
        process_results,
    ):
        # Each sub production unit has only one process. Therefore, there is
        # no need to aggregate results from multiple processes. We just
        # pass on the results from the processes.
        # If required, we could extend the results with results on sub production level.
        results = process_results

        production_cost_in_euro = sub_production_unit.production_cost_in_euro(
            year,
            self._co2_cost_in_euro_per_t_co2,
            self._interest_rate,
            self._simulation_options,
        )
        self._add_entry(
            self._absolute_results['process_production_cost_in_euro'],
            year,
            production_cost_in_euro,
        )

        return results

    def enter_process(self, process, year):
        super().enter_process(process, year)
        # this call should be here in the enter function because its interim results might be used in enter_output
        enter_results = self._collect_process_results(year)
        return enter_results

    def exit_output(
        self,
        output,
        year,
        _enter_results,
    ):
        output_results = self._collect_output_results(output, year)
        return output_results

    def _handle_site_purchased_carrier_amounts(self, purchased_carrier_amounts, year):
        for carrier, purchased_carrier_amount in purchased_carrier_amounts.items():
            carrier_unit = carrier.unit
            if carrier_unit == CarrierUnit.GJ:
                id_energy_carrier = carrier.id
                self._add_site_energy_carrier_entry(
                    self._absolute_results['site_energy_carrier_purchased_amount_in_gj'],
                    id_energy_carrier,
                    year,
                    purchased_carrier_amount,
                )
            elif carrier_unit == CarrierUnit.T:
                if isinstance(carrier, Product):
                    id_product = carrier.id
                    self._add_site_product_entry(
                        self._absolute_results['site_product_purchased_amount_in_t'],
                        id_product,
                        year,
                        purchased_carrier_amount,
                    )
                elif isinstance(carrier, ByProduct):
                    id_by_product = carrier.id
                    self._add_site_by_product_entry(
                        self._absolute_results['site_by_product_purchased_amount_in_t'],
                        id_by_product,
                        year,
                        purchased_carrier_amount,
                    )
                else:
                    message = f'Carrier {type(carrier)} not yet implemented'
                    raise NotImplementedError(message)
            else:
                message = f'Unknown carrier unit {carrier_unit}'
                raise ValueError(message)

    def _handle_production_unit_carrier_result(
        self,
        carrier_dictionary,
        result_name,
        year,
        append_unit=False,
    ):
        for carrier, value in carrier_dictionary.items():
            carrier_unit = carrier.unit
            if carrier_unit == CarrierUnit.GJ:
                id_energy_carrier = carrier.id
                table_name = f'production_unit_energy_carrier_{result_name}'
                if append_unit:
                    table_name += '_in_gj'
                self._add_production_unit_energy_carrier_entry(
                    self._absolute_results[table_name],
                    id_energy_carrier,
                    year,
                    value,
                )
                self._add_region_and_sector_energy_carrier_aggregates(
                    result_name,
                    id_energy_carrier,
                    year,
                    value,
                    append_unit=append_unit,
                )
            elif carrier_unit == CarrierUnit.T:
                if isinstance(carrier, Product):
                    id_product = carrier.id
                    table_name = f'production_unit_product_{result_name}'
                    if append_unit:
                        table_name += '_in_t'
                    self._add_production_unit_product_entry(
                        self._absolute_results[table_name],
                        id_product,
                        year,
                        value,
                    )
                elif isinstance(carrier, ByProduct):
                    id_by_product = carrier.id
                    table_name = f'production_unit_by_product_{result_name}'
                    if append_unit:
                        table_name += '_in_t'
                    self._add_production_unit_by_product_entry(
                        self._absolute_results[table_name],
                        id_by_product,
                        year,
                        value,
                    )
                else:
                    message = f'Carrier {type(carrier)} not yet implemented'
                    raise NotImplementedError(message)
            else:
                message = f'Unknown carrier unit {carrier_unit}'
                raise ValueError(message)

    def _carrier_emission_cost_in_euro(self, emission_in_t_co2_by_carrier, sign=1):
        return {
            carrier: sign * emission_in_t_co2 * self._co2_cost_in_euro_per_t_co2
            for carrier, emission_in_t_co2 in emission_in_t_co2_by_carrier.items()
        }

    def _add_region_and_sector_energy_carrier_aggregates(self, result_name, id_energy_carrier, year, value, *, append_unit):
        if result_name not in self._region_and_sector_energy_carrier_result_names():
            return

        if result_name == 'purchased_amount':
            region_table_name = 'region_energy_carrier_purchased_amount_in_gj'
            sector_table_name = 'sector_energy_carrier_purchased_amount_in_gj'

            self._add_region_energy_carrier_entry_or_accumulate(
                self._absolute_results[region_table_name],
                id_energy_carrier,
                year,
                value,
            )
            self._add_sector_energy_carrier_entry_or_accumulate(
                self._absolute_results[sector_table_name],
                id_energy_carrier,
                year,
                value,
            )
            return

        self._add_region_entry_or_accumulate(
            self._absolute_results[f'region_{result_name}'],
            year,
            value,
        )
        self._add_sector_entry_or_accumulate(
            self._absolute_results[f'sector_{result_name}'],
            year,
            value,
        )

    @staticmethod
    def _region_and_sector_energy_carrier_result_names():
        return {
            'purchased_amount',
            'upstream_emission_in_t_co2',
            'downstream_emission_in_t_co2',
            'renewably_bound_co2_emission_in_t_co2',
        }

    def _add_process_emission_aggregates(self, metric_name, year, value):
        self._add_region_entry_or_accumulate(
            self._absolute_results[f'region_{metric_name}'],
            year,
            value,
        )
        self._add_sector_entry_or_accumulate(
            self._absolute_results[f'sector_{metric_name}'],
            year,
            value,
        )

    def _collect_process_results(self, year):
        interest_rate = self._interest_rate
        simulation_options = self._simulation_options

        process_execution_count = self._collect_process_execution_count(year)

        self._collect_process_direct_emission_in_t_co2(year, process_execution_count)

        self._collect_process_direct_energy_emission_in_t_co2(year, process_execution_count)

        self._collect_process_captured_emission_in_t_co2(year, process_execution_count)

        self._collect_process_direct_non_energy_emission_cost_in_euro(year, process_execution_count)

        self._collect_process_saving_due_to_captured_emission_in_euro(year, process_execution_count)

        self._collect_process_investment_in_euro(year, simulation_options)

        self._collect_process_annuity_on_investment_in_euro_per_count(year, interest_rate, simulation_options)

        self._collect_process_annuity_on_investment_in_euro(year, interest_rate, simulation_options)

        self._collect_process_opex_in_euro_per_process_count(year, simulation_options)

        self._collect_process_opex_in_euro(year, simulation_options)

        self._collect_process_direct_emission_cost_in_euro(year, process_execution_count)
        self._collect_process_direct_energy_emission_cost_in_euro(year, process_execution_count)
        self._collect_process_direct_non_energy_emission_in_t_co2(year, process_execution_count)
        self._collect_process_carrier_cost_in_euro_per_process_count(year)

        self._collect_process_energy_carrier_production_direct_emission_in_t_co2(year, process_execution_count)

        for demand in self._process.demands:
            self._collect_demand_results(
                year,
                demand,
                process_execution_count,
            )

        # placeholder for interim process results that could be used
        # by enter_output or should be aggregated by the visitor to be used on higher levels
        interim_process_results = {}

        return interim_process_results

    def _collect_process_energy_carrier_production_direct_emission_in_t_co2(self, year, process_execution_count):
        energy_carrier_production_direct_emissions = self._process.emission.energy_carrier_production_direct_emissions_in_t_co2(
            process_execution_count
        )
        for carrier, emission in energy_carrier_production_direct_emissions.items():
            id_energy_carrier = carrier.id
            self._add_energy_carrier_entry(
                self._absolute_results['process_energy_carrier_production_direct_emission_in_t_co2'],
                id_energy_carrier,
                year,
                emission,
            )

    def _collect_process_execution_count(self, year):
        process_execution_count = self._sub_production_unit.process_execution_count
        self._add_entry(
            self._absolute_results['process_execution_count'],
            year,
            process_execution_count,
        )
        return process_execution_count

    def _collect_process_carrier_cost_in_euro_per_process_count(self, year):
        value = self._process.purchase_cost_in_euro_per_process_count(year)

        self._add_entry(
            self._specific_results['process_carrier_cost_in_euro_per_process_count'],
            year,
            value,
        )

    def _collect_process_opex_in_euro(self, year, simulation_options):
        process_opex_in_euro = self._sub_production_unit.opex_in_euro(year, simulation_options)
        self._add_entry(
            self._absolute_results['process_opex_in_euro'],
            year,
            process_opex_in_euro,
        )

    def _collect_process_opex_in_euro_per_process_count(self, year, simulation_options):
        process_opex_in_euro_per_process_count = self._process.opex_in_euro_per_process_count(year, simulation_options)
        self._add_entry(
            self._specific_results['process_opex_in_euro_per_process_count'],
            year,
            process_opex_in_euro_per_process_count,
        )

    def _collect_process_annuity_on_investment_in_euro(self, year, interest_rate, simulation_options):
        process_annuity_on_investment_in_euro = self._sub_production_unit.annuity_on_investment_in_euro(
            year, interest_rate, simulation_options
        )
        self._add_entry(
            self._absolute_results['process_annuity_on_investment_in_euro'],
            year,
            process_annuity_on_investment_in_euro,
        )

    def _collect_process_annuity_on_investment_in_euro_per_count(
        self,
        year,
        interest_rate,
        simulation_options,
    ):
        process_annuity_on_investment_in_euro_per_process_count = self._process.annuity_on_investment_in_euro_per_process_count(
            year, interest_rate, simulation_options
        )
        self._add_entry(
            self._specific_results['process_annuity_on_investment_in_euro_per_process_count'],
            year,
            process_annuity_on_investment_in_euro_per_process_count,
        )

    def _collect_demand_results(
        self,
        year,
        demand,
        process_execution_count,
    ):
        carrier = demand.carrier
        carrier_purchase_cost_in_euro_per_process_count = demand.purchase_cost_in_euro_per_process_count(year)

        carrier_unit = carrier.unit
        if carrier_unit == CarrierUnit.GJ:
            self._handle_energy_carrier_demand(
                year,
                demand,
                process_execution_count,
                carrier_purchase_cost_in_euro_per_process_count,
            )

        elif carrier_unit == CarrierUnit.T:
            if isinstance(carrier, Product):
                self._handle_product_demand(
                    year,
                    demand,
                    process_execution_count,
                    carrier_purchase_cost_in_euro_per_process_count,
                )

            elif isinstance(carrier, ByProduct):
                self._handle_by_product_demand(
                    year,
                    demand,
                    process_execution_count,
                    carrier_purchase_cost_in_euro_per_process_count,
                )

            else:
                message = f'Carrier {type(carrier)} not yet implemented'
                raise NotImplementedError(message)

        else:
            message = f'Unknown carrier unit {carrier_unit}'
            raise ValueError(message)

    def _handle_energy_carrier_demand(
        self,
        year,
        demand,
        process_execution_count,
        carrier_purchase_cost_in_euro_per_process_count,
    ):
        energy_carrier = demand.carrier
        id_energy_carrier = energy_carrier.id

        if isinstance(demand, EnergyCarrierEnergyDemand):
            # energy carrier purchase cost in euro per count
            self._add_energy_carrier_entry(
                self._specific_results['process_energy_carrier_energy_purchase_cost_in_euro_per_process_count'],
                id_energy_carrier,
                year,
                carrier_purchase_cost_in_euro_per_process_count,
            )

            # energy carrier energy demand in gj
            energy_carrier_energy_demand_in_gj = demand.demand_in_gj(year, process_execution_count)

            self._add_energy_carrier_entry(
                self._absolute_results['process_energy_carrier_energy_demand_in_gj'],
                id_energy_carrier,
                year,
                energy_carrier_energy_demand_in_gj,
            )

            # energy carrier direct energy emission in t co2
            energy_carrier_demand_direct_emission_in_t_co2 = demand.direct_emission_in_t_co2(year, process_execution_count)

            self._add_energy_carrier_entry(
                self._absolute_results['process_energy_carrier_energy_demand_direct_emission_in_t_co2'],
                id_energy_carrier,
                year,
                energy_carrier_demand_direct_emission_in_t_co2,
            )
        else:
            self._add_energy_carrier_entry(
                self._specific_results['process_energy_carrier_feedstock_purchase_cost_in_euro_per_process_count'],
                id_energy_carrier,
                year,
                carrier_purchase_cost_in_euro_per_process_count,
            )

            # energy carrier feedstock demand in gj
            energy_carrier_feedstock_demand_in_gj = demand.demand_in_gj(year, process_execution_count)

            self._add_energy_carrier_entry(
                self._absolute_results['process_energy_carrier_feedstock_demand_in_gj'],
                id_energy_carrier,
                year,
                energy_carrier_feedstock_demand_in_gj,
            )

    def _handle_by_product_demand(
        self,
        year,
        demand,
        process_execution_count,
        carrier_purchase_cost_in_euro_per_process_count,
    ):
        by_product = demand.carrier
        id_by_product = by_product.id

        # by_product purchase cost in euro per count
        self._add_product_entry(
            self._specific_results['process_by_product_purchase_cost_in_euro_per_process_count'],
            id_by_product,
            year,
            carrier_purchase_cost_in_euro_per_process_count,
        )

        # by_product demand in t
        by_product_demand_in_t = demand.demand_in_t(year, process_execution_count)
        self._add_product_entry(
            self._absolute_results['process_by_product_feedstock_demand_in_t'],
            id_by_product,
            year,
            by_product_demand_in_t,
        )

    def _handle_product_demand(
        self,
        year,
        demand,
        process_execution_count,
        carrier_purchase_cost_in_euro_per_process_count,
    ):
        product = demand.carrier
        id_product = product.id

        # product purchase cost in euro per count
        self._add_product_entry(
            self._specific_results['process_product_purchase_cost_in_euro_per_process_count'],
            id_product,
            year,
            carrier_purchase_cost_in_euro_per_process_count,
        )

        # product demand in t
        product_demand_in_t = demand.demand_in_t(year, process_execution_count)
        self._add_product_entry(
            self._absolute_results['process_product_feedstock_demand_in_t'],
            id_product,
            year,
            product_demand_in_t,
        )

    def _collect_output_results(self, output, year):
        process_execution_count = self._sub_production_unit.process_execution_count

        if self._id_energy_carrier is not None:
            production_in_gj = output.output_in_gj(process_execution_count)

            self._add_energy_carrier_entry(
                self._absolute_results['process_energy_carrier_production_in_gj'],
                self._id_energy_carrier,
                year,
                production_in_gj,
            )
        else:
            production_in_t = output.output_in_t(process_execution_count)
            if self._id_product is not None:
                self._add_product_entry(
                    self._absolute_results['process_product_production_in_t'],
                    self._id_product,
                    year,
                    production_in_t,
                )
            elif self._id_by_product is not None:
                self._add_by_product_entry(
                    self._absolute_results['process_by_product_production_in_t'],
                    self._id_by_product,
                    year,
                    production_in_t,
                )
            else:
                message = 'Neither energy carrier nor product nor by-product id is set'
                raise ValueError(message)

        self._collect_production_cost_in_euro_per_process_count(output, year)

        # placeholder for interim output results that could be aggregated and used on higher levels of the visitor
        output_results = {}

        return output_results

    def _collect_production_cost_in_euro_per_process_count(
        self,
        output,
        year,
    ):
        production_cost_in_euro_per_process_count = self._process.production_cost_in_euro_per_process_count(
            year, self._interest_rate, self._simulation_options
        )

        carrier = output.carrier
        if isinstance(carrier, Product):
            self._add_product_entry(
                self._specific_results['process_product_production_cost_in_euro_per_process_count'],
                self._id_product,
                year,
                production_cost_in_euro_per_process_count,
            )
        elif isinstance(carrier, ByProduct):
            self._add_by_product_entry(
                self._specific_results['process_by_product_production_cost_in_euro_per_process_count'],
                self._id_by_product,
                year,
                production_cost_in_euro_per_process_count,
            )
        elif isinstance(carrier, EnergyCarrier):
            self._add_energy_carrier_entry(
                self._specific_results['process_energy_carrier_production_cost_in_euro_per_process_count'],
                self._id_energy_carrier,
                year,
                production_cost_in_euro_per_process_count,
            )
        else:
            message = f'Carrier {type(carrier)} not yet implemented'
            raise NotImplementedError(message)

    def _collect_process_investment_in_euro(self, year, simulation_options):
        new_investment_in_euro = self._sub_production_unit.new_investment_in_euro(year, simulation_options)
        self._add_entry(
            self._absolute_results['process_investment_in_euro'],
            year,
            new_investment_in_euro,
        )
        logging.debug('Investment %s in %s', new_investment_in_euro, year)

    def _collect_process_direct_emission_in_t_co2(self, year, process_execution_count):
        process_direct_emission = self._process.emission.direct_emissions_in_t_co2(
            year,
            process_execution_count,
        )
        self._add_entry(
            self._absolute_results['process_direct_emission_in_t_co2'],
            year,
            process_direct_emission,
        )
        self._add_process_emission_aggregates('direct_emission_in_t_co2', year, process_direct_emission)
        logging.debug('Process direct emissions in t_co2 %s in %s', process_direct_emission, year)

    def _collect_process_direct_emission_cost_in_euro(self, year, process_execution_count):
        process_direct_emission_cost_in_euro = self._process.emission.direct_emission_cost_in_euro(
            year,
            process_execution_count,
            self._co2_cost_in_euro_per_t_co2,
        )

        self._add_entry(
            self._absolute_results['process_direct_emission_cost_in_euro'],
            year,
            process_direct_emission_cost_in_euro,
        )

        logging.debug(
            'Process direct emission cost in euro %s in %s',
            process_direct_emission_cost_in_euro,
            year,
        )

    def _collect_process_direct_energy_emission_in_t_co2(self, year, process_execution_count):
        process_direct_energy_emission = self._process.emission.direct_energy_emissions_in_t_co2(year, process_execution_count)
        self._add_entry(
            self._absolute_results['process_direct_energy_emission_in_t_co2'],
            year,
            process_direct_energy_emission,
        )
        logging.debug(
            'Process direct energy emissions in t_co2 %s in %s',
            process_direct_energy_emission,
            year,
        )

    def _collect_process_direct_energy_emission_cost_in_euro(self, year, process_execution_count):
        process_direct_energy_emission_cost_in_euro = self._process.emission.direct_energy_emission_cost_in_euro(
            year,
            process_execution_count,
            self._co2_cost_in_euro_per_t_co2,
        )

        self._add_entry(
            self._absolute_results['process_direct_energy_emission_cost_in_euro'],
            year,
            process_direct_energy_emission_cost_in_euro,
        )

        logging.debug(
            'Process direct energy emission cost in euro %s in %s',
            process_direct_energy_emission_cost_in_euro,
            year,
        )

    def _collect_process_direct_non_energy_emission_in_t_co2(self, year, process_execution_count):
        process_direct_non_energy_emission = self._process.emission.direct_non_energy_emissions_in_t_co2(process_execution_count)
        self._add_entry(
            self._absolute_results['process_direct_non_energy_emission_in_t_co2'],
            year,
            process_direct_non_energy_emission,
        )
        logging.debug(
            'Process direct non energy emissions in t_co2 %s in %s',
            process_direct_non_energy_emission,
            year,
        )
        return process_direct_non_energy_emission

    def _collect_process_direct_non_energy_emission_cost_in_euro(self, year, process_execution_count):
        process_direct_non_energy_emission_cost_in_euro = self._process.emission.direct_non_energy_emission_cost_in_euro(
            process_execution_count, self._co2_cost_in_euro_per_t_co2
        )

        self._add_entry(
            self._absolute_results['process_direct_non_energy_emission_cost_in_euro'],
            year,
            process_direct_non_energy_emission_cost_in_euro,
        )

        logging.debug(
            'Process direct energy emission cost in euro %s in %s',
            process_direct_non_energy_emission_cost_in_euro,
            year,
        )

    def _collect_process_captured_emission_in_t_co2(self, year, process_execution_count):
        process_captured_emission = self._process.emission.captured_emission_in_t_co2(process_execution_count)
        self._add_entry(
            self._absolute_results['process_captured_emission_in_t_co2'],
            year,
            process_captured_emission,
        )
        self._add_process_emission_aggregates('captured_emission_in_t_co2', year, process_captured_emission)
        logging.debug(
            'Process captured emission in t_co2 %s in %s',
            process_captured_emission,
            year,
        )

    def _collect_process_saving_due_to_captured_emission_in_euro(self, year, process_execution_count):
        process_saving_due_to_captured_emission_in_euro = self._process.emission.saving_due_to_captured_emission_in_euro(
            process_execution_count, self._co2_cost_in_euro_per_t_co2
        )

        self._add_entry(
            self._absolute_results['process_saving_due_to_captured_emission_in_euro'],
            year,
            process_saving_due_to_captured_emission_in_euro,
        )

        logging.debug(
            'Process saving due to captured emission in euro %s in %s',
            process_saving_due_to_captured_emission_in_euro,
            year,
        )

