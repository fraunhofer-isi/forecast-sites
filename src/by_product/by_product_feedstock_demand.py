# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from demand.demand import Demand


class ByProductFeedstockDemand(Demand):
    def __init__(
        self,
        by_product,
        demand_in_t_per_process_count,
        efficiency_improvement_interpolation_data,
        simulation_options,
    ):
        super().__init__(
            by_product,
            efficiency_improvement_interpolation_data,
            simulation_options,
        )
        self._raw_demand_in_t_per_process_count = demand_in_t_per_process_count

    @property
    def by_product(self):
        return self.carrier

    def demand_in_t_per_process_count(self, year):
        efficiency_factor = self._efficiency_factor(year)
        demand = self._raw_demand_in_t_per_process_count * efficiency_factor
        return demand

    def demand_in_t(self, year, process_execution_count):
        demand = self.demand_in_t_per_process_count(year) * process_execution_count
        return demand

    def purchase_cost_in_euro_per_process_count(self, year):
        return self._raw_purchase_cost_in_euro_per_process_count(year)

    def opportunity_cost_in_euro_per_process_count(self, year, co2_price_in_euro_per_t_co2):
        demand = self.demand_in_t_per_process_count(year)
        price = self.by_product.sell_price_in_euro_per_t(year)
        downstream_emission = self.by_product.downstream_emission_in_t_co2_per_unit(year, self._simulation_options)
        emission_adjusted_price = price - downstream_emission * co2_price_in_euro_per_t_co2
        sell_price_in_euro_per_process_count = demand * emission_adjusted_price
        return sell_price_in_euro_per_process_count

    def subsidies_in_euro_per_process_count(self, _year, _simulation_options):
        return 0

    def taxes_in_euro_per_process_count(self, _year, _simulation_options):
        return 0

    def _raw_purchase_cost_in_euro_per_process_count(self, year):
        demand = self.demand_in_t_per_process_count(year)
        price = self.by_product.purchase_price_in_euro_per_t(year)
        raw_cost_in_euro_per_process_count = demand * price
        return raw_cost_in_euro_per_process_count
