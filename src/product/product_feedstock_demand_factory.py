# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from demand.demand_factory import DemandFactory
from product.product_feedstock_demand import ProductFeedstockDemand


class ProductFeedstockDemandFactory(DemandFactory):
    def __init__(
        self,
        process_product_feedstock_demand,
        products,
        efficiency_improvement_interpolation_data,
        simulation_options,
    ):
        super().__init__(
            process_product_feedstock_demand,
            products,
            efficiency_improvement_interpolation_data,
            simulation_options,
        )

    def _demand(self, row):
        id_product = row.name
        product = self._carriers[id_product]

        demand_in_t_per_process_count = row['demand_in_t_per_process_count']

        demand = ProductFeedstockDemand(
            product,
            demand_in_t_per_process_count,
            self._efficiency_improvement_interpolation_data,
            self._simulation_options,
        )
        return demand
