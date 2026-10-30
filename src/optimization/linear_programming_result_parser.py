# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Parser for converting scipy optimization results to domain objects."""

import logging

from optimization.linear_programming_helper import LinearProgrammingHelper
from optimization.linear_programming_optimization_result import (
    LinearProgrammingOptimizationResult,
)
from utils.time_utils import create_time_span


class LinearProgrammingResultParser:
    """Parses and transforms scipy optimizer results into domain objects."""

    def __init__(self, optimization):
        """
        Initialize the result parser.

        Args:
            optimization: The LinearProgrammingOptimization instance providing context.

        """
        self._optimization = optimization

    def parse_result(self, linear_programming_result, simulation_options):
        """
        Parse scipy optimization result into domain object.

        Args:
            linear_programming_result: The scipy optimize result object.
            simulation_options: Simulation options dictionary.

        Returns:
            LinearProgrammingOptimizationResult instance.

        Raises:
            RuntimeError: If optimization failed.

        """
        if linear_programming_result.success:
            logging.debug('Optimization succeeded')
            optimization_result = LinearProgrammingOptimizationResult(
                linear_programming_result,
                self._optimization._process_options,
                self._optimization._carriers,
                total_cost_in_euro=linear_programming_result.fun,
                modeled_year_count=self._modeled_year_count(self._optimization._year, simulation_options),
                selected_rolling_planning_horizon_in_years=simulation_options['rolling_planning_horizon_in_years'],
                interest_rate=self._optimization._context.interest_rate,
            )
        else:
            message = (
                f'Optimization failed for production_unit {self._optimization._production_unit.id} '
                f'in year {self._optimization._year}!\n{linear_programming_result}'
            )
            raise RuntimeError(message)

        return optimization_result

    @staticmethod
    def _modeled_year_count(current_year, simulation_options):
        """Calculate number of years modeled in optimization."""
        planning_years = LinearProgrammingResultParser._planning_years(current_year, simulation_options)
        return len(planning_years)

    @staticmethod
    def _planning_years(current_year, simulation_options):
        """Get planning years for the optimization horizon."""
        return LinearProgrammingHelper.planning_years(current_year, simulation_options)
