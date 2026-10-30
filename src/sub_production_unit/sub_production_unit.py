# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from result.visitor.entity import Entity


# pylint: disable=too-many-instance-attributes
class SubProductionUnit(Entity):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        id_sub_production_unit,
        id_production_unit,
        process_execution_count,
        max_process_execution_count,
        year_of_last_reinvestment,
    ):
        super().__init__(id_sub_production_unit)
        self._id_production_unit = id_production_unit
        self.installed_process = None  # needs to be set by factory after construction
        self.process_execution_count = process_execution_count
        self.max_process_execution_count = max_process_execution_count
        self.year_of_last_reinvestment = year_of_last_reinvestment

    @property
    def id_production_unit(self):
        """Explicit semantic access to the ID of the owning production unit."""
        return self._id_production_unit

    @id_production_unit.setter
    def id_production_unit(self, value):
        """Re-parent this sub production unit, used when sites are merged into a group."""
        self._id_production_unit = value

    @property
    def used_carriers(self):
        carriers = self.installed_process.used_carriers
        return carriers

    @property
    def output_by_products(self):
        by_products = self.installed_process.output_by_products
        return by_products

    @property
    def id_process(self):
        return self.installed_process.id

    @property
    def demands(self):
        demands = self.installed_process.demands
        return demands

    def accept(self, visitor, year):
        enter_results = visitor.enter_sub_production_unit(self, year)
        child_result = self.installed_process.accept(visitor, year)
        result = visitor.exit_sub_production_unit(
            self,
            year,
            enter_results,
            child_result,
        )
        return result

    def netto_produced_or_consumed_amount_for_carrier(self, year, carrier):
        # Calculates the netto output for a specific carrier by this sub-production unit.
        # A negative value is allowed here and means that the carrier is consumed by the sub-production unit.
        # The unit is in t or GJ, depending on the carrier.
        process_execution_count = self.process_execution_count
        export_per_process_count = self.installed_process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
        netto_amount = process_execution_count * export_per_process_count

        return netto_amount

    def production_cost_in_euro(
        self,
        year,
        co2_cost_in_euro_per_t_co2,
        interest_rate,
        simulation_options,
    ):
        process_production_cost_in_euro = self._process_production_cost_in_euro(year, interest_rate, simulation_options)

        direct_emission_cost_in_euro = self._direct_emission_cost_in_euro(
            year,
            co2_cost_in_euro_per_t_co2,
        )

        cost_in_euro = process_production_cost_in_euro + direct_emission_cost_in_euro

        return cost_in_euro

    def annuity_on_investment_in_euro(self, year, interest_rate, simulation_options):
        if year < self.year_of_last_reinvestment:
            return 0

        annuity_per_process_count = self.installed_process.annuity_on_investment_in_euro_per_process_count(
            year,
            interest_rate,
            simulation_options,
        )
        annuity_in_euro = self.max_process_execution_count * annuity_per_process_count
        return annuity_in_euro

    def opex_in_euro(self, year, simulation_options):
        opex_per_process_count = self.installed_process.opex_in_euro_per_process_count(year, simulation_options)
        opex = self.process_execution_count * opex_per_process_count
        return opex

    def new_investment_in_euro(self, year, simulation_options):
        if year == self.year_of_last_reinvestment:
            investment_per_process_count = self.installed_process.net_capex_in_euro_per_process_count(year, simulation_options)
            investment = self.max_process_execution_count * investment_per_process_count
        else:
            investment = 0
        return investment

    def number_of_process_usages(self, process):
        # Returns 1 if this sub production unit uses the given processes (by id), else 0
        try:
            id_process = process.id
        except AttributeError:
            return 0
        return 1 if self.installed_process.id == id_process else 0

    def direct_emissions_in_t_co2(self, year):
        # calculates scope 1 emissions
        # Here we assume, that the emissions result only from the
        # processes emissions. If needed, further aspects could be added in the future.
        emissions = self.installed_process.emission.direct_emissions_in_t_co2(year, self.process_execution_count)
        return emissions

    def emissions_in_t_co2(self):
        # dummy function to give a hint upstream and total emissions are not available on
        # the level of sub production units. Until now, upstream emissions are only calculated
        # on the level of production units.
        message = (
            'Until now, we calculate scope 3 emissions only on level of production unit'
            'If you want to consider them on lower levels, you need to calculate them as nested sum.'
        )

        raise NotImplementedError(message)

    def _process_production_cost_in_euro(self, year, interest_rate, simulation_options):
        process_production_cost_per_process_count = self.installed_process.production_cost_in_euro_per_process_count(
            year, interest_rate, simulation_options
        )
        process_production_cost_in_euro = self.process_execution_count * process_production_cost_per_process_count
        return process_production_cost_in_euro

    def _direct_emission_cost_in_euro(self, year, co2_cost_in_euro_per_t_co2):
        direct_emission_cost_in_euro = (
            self.process_execution_count
            * self.installed_process.emission.direct_emissions_in_t_co2_per_process_count(year)
            * co2_cost_in_euro_per_t_co2
        )
        return direct_emission_cost_in_euro

    def _uses_carrier(self, carrier_type, id_carrier):
        return any(isinstance(carrier, carrier_type) and carrier.id == id_carrier for carrier in self.used_carriers)
