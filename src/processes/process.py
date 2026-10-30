# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from interpolation import interpolator
from processes.abstract_process import AbstractProcess
from processes.process_data_spec import ProcessDataSpec
from processes.process_emission import ProcessEmission
from utils.collection_utils import object_sum


class Process(AbstractProcess, ProcessDataSpec):
    def __init__(self, id_process, process_data):
        self._emission = ProcessEmission(self)
        # The super __init__ method needs to be called after setting the class attributes because
        # we inherit from PartialImmutable. Otherwise, the attribute(s) could not be set.
        super().__init__(id_process, process_data)

    @property
    def emission(self):
        return self._emission

    def annual_cost_in_euro_per_process_count(
        self,
        year,
        co2_price_in_euro_per_t_co2,
        simulation_options,
    ):
        # This method is used by the linear programming objective function
        opex_in_euro_per_process_count = self.opex_in_euro_per_process_count(year, simulation_options)

        production_gain_in_euro_per_process_count = self._value_added_in_euro_per_process_count(
            year, co2_price_in_euro_per_t_co2, simulation_options
        )

        direct_emission_cost_in_euro_per_process_count = self.emission.direct_emission_cost_in_euro_per_process_count(
            year,
            co2_price_in_euro_per_t_co2,
        )

        savings_due_to_captured_emissions_in_euro_per_process_count = (
            self.emission.savings_due_to_captured_emissions_in_euro_per_process_count(co2_price_in_euro_per_t_co2)
        )

        cost = (
            opex_in_euro_per_process_count
            - production_gain_in_euro_per_process_count
            + direct_emission_cost_in_euro_per_process_count
            - savings_due_to_captured_emissions_in_euro_per_process_count
        )

        return cost

    def annuity_on_investment_in_euro_per_process_count(self, year, interest_rate, simulation_options):
        net_capex = self.net_capex_in_euro_per_process_count(year, simulation_options)
        annuity_factor = self._annuity_factor(interest_rate)
        annuity = annuity_factor * net_capex
        return annuity

    def invest_cost_in_euro_per_process_count(
        self,
        current_year,
        _interest_rate,
        simulation_options,
        capex_factor=1.0,
    ):
        # CAPEX net of investment funding, incurred in full when the process is built (not pro-rated across years).
        return self.net_capex_in_euro_per_process_count(current_year, simulation_options, capex_factor)

    def net_capex_in_euro_per_process_count(self, year, simulation_options, capex_factor=1.0):
        """
        Return the CAPEX that has to be paid by the investor.

        The capex_factor scales the CAPEX before the investment funding is deducted;
        see ProcessFinancialCalculator.net_investment for why that ordering matters.
        """
        capex = self.capex_in_euro_per_process_count(year, simulation_options)
        funding = self.investment_funding_in_euro_per_process_count(year, simulation_options)
        return self._financial_calc.net_investment(capex, funding, capex_factor)

    def production_cost_in_euro_per_process_count(self, year, interest_rate, simulation_options):
        cost = (
            self.annuity_on_investment_in_euro_per_process_count(year, interest_rate, simulation_options)
            + self.opex_in_euro_per_process_count(year, simulation_options)
            + self.purchase_cost_in_euro_per_process_count(year)
        )
        return cost

    def purchase_cost_in_euro_per_process_count(self, year):
        carrier_cost = object_sum(
            self.demands,
            lambda demand: demand.purchase_cost_in_euro_per_process_count(year),
        )

        return carrier_cost

    def capex_in_euro_per_process_count(self, year, simulation_options):
        return interpolator.interpolate(
            year,
            simulation_options,
            self.capex_interpolation_data_in_euro_per_process_count,
        )

    def opex_in_euro_per_process_count(self, year, simulation_options):
        return interpolator.interpolate(
            year,
            simulation_options,
            self.opex_interpolation_data_in_euro_per_process_count,
        )

    def subsidies_in_euro_per_process_count(self, year, simulation_options):
        subsidies = object_sum(
            self.demands,
            lambda demand: demand.subsidies_in_euro_per_process_count(year, simulation_options),
        )

        return subsidies

    def taxes_in_euro_per_process_count(self, year, simulation_options):
        taxes = object_sum(
            self.demands,
            lambda demand: demand.taxes_in_euro_per_process_count(year, simulation_options),
        )

        return taxes

    def _efficiency_improvement(self, year, simulation_options):
        return interpolator.interpolate(
            year,
            simulation_options,
            self.efficiency_improvement_interpolation_data,
        )

    def investment_funding_in_euro_per_process_count(
        self,
        year,
        simulation_options,
    ):
        return interpolator.interpolate(
            year,
            simulation_options,
            self.investment_funding_interpolation_data_in_euro_per_process_count,
        )
    def _value_added_in_euro_per_process_count(self, year, co2_price_in_euro_per_t_co2, simulation_options):
        production_gain = 0

        for output in self.outputs:
            output_in_euro_per_process_count = output.output_in_euro_per_process_count(
                year, co2_price_in_euro_per_t_co2, simulation_options
            )
            production_gain += output_in_euro_per_process_count

        for demand in self.demands:
            input_in_euro_per_process_count = demand.opportunity_cost_in_euro_per_process_count(
                year,
                co2_price_in_euro_per_t_co2,
            )
            production_gain -= input_in_euro_per_process_count

        return production_gain
