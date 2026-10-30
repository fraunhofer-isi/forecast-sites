# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from demand.demand import Demand


class EnergyCarrierFeedstockDemand(Demand):
    def __init__(
        self,
        energy_carrier,
        demand_in_gj_per_process_count,
        efficiency_improvement_interpolation_data,
        simulation_options,
    ):
        super().__init__(
            energy_carrier,
            efficiency_improvement_interpolation_data,
            simulation_options,
        )
        self._raw_demand_in_gj_per_process_count = demand_in_gj_per_process_count

    @property
    def energy_carrier(self):
        return self.carrier

    def demand_in_gj_per_process_count(self, year):
        efficiency_factor = self._efficiency_factor(year)
        demand = self._raw_demand_in_gj_per_process_count * efficiency_factor
        return demand

    def demand_in_gj(self, year, process_execution_count):
        demand = process_execution_count * self.demand_in_gj_per_process_count(year)
        return demand

    def purchase_cost_in_euro_per_process_count(self, year):
        return self._raw_purchase_cost_in_euro_per_process_count(year)

    def _raw_purchase_cost_in_euro_per_process_count(self, year):
        demand = self.demand_in_gj_per_process_count(year)
        price = self.energy_carrier.purchase_price_in_euro_per_gj(year)
        raw_cost_in_euro_per_process_count = demand * price
        return raw_cost_in_euro_per_process_count

    def opportunity_cost_in_euro_per_process_count(self, year, co2_price_in_euro_per_t_co2):
        demand = self.demand_in_gj_per_process_count(year)
        price = self.energy_carrier.sell_price_in_euro_per_gj(year)
        downstream_emission = self.energy_carrier.downstream_emission_in_t_co2_per_unit(year, self._simulation_options)
        emission_adjusted_price = price - downstream_emission * co2_price_in_euro_per_t_co2
        cost_in_euro_per_process_count = demand * emission_adjusted_price
        return cost_in_euro_per_process_count

    def purchase_cost_in_euro(self, year, process_execution_count):
        purchase_cost_in_euro_per_process_count = self.purchase_cost_in_euro_per_process_count(year)
        purchase_cost = process_execution_count * purchase_cost_in_euro_per_process_count
        return purchase_cost

    def subsidies_in_euro_per_process_count(self, year, simulation_options):
        demand = self.demand_in_gj_per_process_count(year)
        subsidies_in_euro_per_gj = self.energy_carrier.subsidies_in_euro_per_gj(year, simulation_options)
        subsidies_in_euro_per_t = demand * subsidies_in_euro_per_gj
        return subsidies_in_euro_per_t

    def taxes_in_euro_per_process_count(self, year, simulation_options):
        demand = self.demand_in_gj_per_process_count(year)
        taxes_in_euro_per_gj = self.energy_carrier.taxes_in_euro_per_gj(year, simulation_options)
        taxes_in_euro_per_process_count = demand * taxes_in_euro_per_gj
        return taxes_in_euro_per_process_count
