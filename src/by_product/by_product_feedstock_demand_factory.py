# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from by_product.by_product_feedstock_demand import ByProductFeedstockDemand
from demand.demand_factory import DemandFactory


class ByProductFeedstockDemandFactory(DemandFactory):
    def __init__(
        self,
        process_by_product_feedstock_demand,
        by_products,
        efficiency_improvement_interpolation_data,
        simulation_options,
    ):
        super().__init__(
            process_by_product_feedstock_demand,
            by_products,
            efficiency_improvement_interpolation_data,
            simulation_options,
        )

    def _demand(self, row):
        id_by_product = row.name
        by_product = self._carriers[id_by_product]

        demand_in_t_per_process_count = row['demand_in_t_per_process_count']

        demand = ByProductFeedstockDemand(
            by_product,
            demand_in_t_per_process_count,
            self._efficiency_improvement_interpolation_data,
            self._simulation_options,
        )
        return demand
