# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from optimization.linear_programming_optimization import LinearProgrammingOptimization
from optimization.optimization import Optimization
from optimization.optimization_context import OptimizationContext

logger = logging.getLogger(__name__)


class ComparingOptimization(Optimization):
    def __init__(self, year, production_unit, context):
        super().__init__(year, production_unit, context)

    def optimize(self):
        simulation_options = self._context.simulation_options
        short_horizon_in_years = simulation_options['year_increment']
        long_horizon_in_years = simulation_options['rolling_planning_horizon_in_years']

        if short_horizon_in_years == long_horizon_in_years:
            return self._optimization_result_for_horizon(short_horizon_in_years)

        short_horizon_result = self._optimization_result_for_horizon(short_horizon_in_years)
        long_horizon_result = self._optimization_result_for_horizon(long_horizon_in_years)

        return self._better_result(short_horizon_result, long_horizon_result)

    def _optimization_result_for_horizon(self, rolling_planning_horizon_in_years):
        comparison_context = self._context_with_horizon(rolling_planning_horizon_in_years)
        optimization = LinearProgrammingOptimization(self._year, self._production_unit, comparison_context)
        return optimization.optimize()

    def _context_with_horizon(self, rolling_planning_horizon_in_years):
        simulation_options = dict(self._context.simulation_options)
        simulation_options['rolling_planning_horizon_in_years'] = rolling_planning_horizon_in_years

        comparison_context = OptimizationContext(
            self._context.co2_cost_in_euro_per_t_co2,
            self._context.interest_rate,
            simulation_options,
        )

        if hasattr(self._context, 'site'):
            comparison_context.site = self._context.site

        return comparison_context

    def _better_result(self, first_result, second_result):
        logger.info('Short term: %s', first_result.cost_per_year_in_euro)
        logger.info('Long term: %s', second_result.cost_per_year_in_euro)
        if first_result.cost_per_year_in_euro < second_result.cost_per_year_in_euro:
            logger.info('Short term (%s)', self._year)
            return first_result

        if second_result.cost_per_year_in_euro < first_result.cost_per_year_in_euro:
            logger.info('Long term (%s)', self._year)
            return second_result

        if first_result.selected_rolling_planning_horizon_in_years >= second_result.selected_rolling_planning_horizon_in_years:
            return first_result

        return second_result
