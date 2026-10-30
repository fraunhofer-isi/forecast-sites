# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from region.region_new_capacity_adapter import _RegionNewCapacityAdapter


class RegionResultApplier:
    def apply(self, year, region_result, production_units, context):
        self._assign_results(region_result, production_units)
        self._update_sub_production_units(year, production_units)
        pool_deltas = self._aggregate_pool_deltas(year, production_units)
        self._apply_pool_deltas(year, pool_deltas, context)

    def apply_for_year(self, year, multi_period_result, production_units, context):
        """Apply a multi-period result for a specific year, including vintage creation."""
        self._assign_results_for_year(year, multi_period_result, production_units)
        self._update_sub_production_units_from_multi_period(year, multi_period_result, production_units)
        pool_deltas = self._aggregate_pool_deltas(year, production_units)
        self._apply_pool_deltas(year, pool_deltas, context)

    def _assign_results(self, region_result, production_units):
        for production_unit in production_units:
            production_unit.optimization_results = region_result.result_for(production_unit)

    def _assign_results_for_year(self, year, multi_period_result, production_units):
        for production_unit in production_units:
            production_unit.optimization_results = multi_period_result.result_for(production_unit, year)

    def _update_sub_production_units(self, year, production_units):
        for production_unit in production_units:
            production_unit._create_or_update_sub_production_units(year)

    def _update_sub_production_units_from_multi_period(self, year, multi_period_result, production_units):
        new_capacity_by_pu = multi_period_result.new_capacity_for_year(year)
        for production_unit in production_units:
            pu_new_capacity = new_capacity_by_pu.get(production_unit, {})
            production_unit._multi_period_result = _RegionNewCapacityAdapter(pu_new_capacity)
            production_unit._create_or_update_sub_production_units_from_multi_period(year)
            production_unit._multi_period_result = None

    def _aggregate_pool_deltas(self, year, production_units):
        deltas = {}

        for production_unit in production_units:
            site = production_unit._site

            for carrier, amount in production_unit.purchased_carrier_amounts.items():
                if amount == 0:
                    continue
                pool = site.shared_pool_for(carrier)
                key = (pool, carrier)
                deltas.setdefault(key, 0.0)
                deltas[key] += amount

        return deltas


    def _apply_pool_deltas(self, year, pool_deltas, context):
        for (pool, carrier), consumed in pool_deltas.items():
            if consumed > 0:
                pool.consume_purchased_carrier_amount(carrier, consumed, year, context)
