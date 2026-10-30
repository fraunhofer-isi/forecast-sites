# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from optimization.optimization_result import OptimizationResult


class LinearProgrammingOptimizationResult(OptimizationResult):
    def __init__(
        self,
        linear_programming_result,
        process_options,
        carriers,
        total_cost_in_euro=None,
        modeled_year_count=None,
        selected_rolling_planning_horizon_in_years=None,
        interest_rate=None,
    ):
        process_execution_counts = self._process_execution_counts(linear_programming_result, process_options)
        purchased_carrier_amounts = self._purchased_carrier_amounts(linear_programming_result, process_options, carriers)
        super().__init__(
            process_execution_counts,
            purchased_carrier_amounts,
            total_cost_in_euro,
            modeled_year_count,
            selected_rolling_planning_horizon_in_years,
            interest_rate,
        )

    @staticmethod
    def _process_execution_counts(linear_programming_result, process_options):
        solution_values = linear_programming_result.x

        number_of_process_options = len(process_options)
        raw_process_execution_counts = solution_values[:number_of_process_options]

        process_execution_counts = {
            process_option: float(count)
            for process_option, count in zip(process_options, raw_process_execution_counts, strict=False)
        }
        logging.debug('Process execution counts: %s', process_execution_counts)
        return process_execution_counts

    @staticmethod
    def _purchased_carrier_amounts(linear_programming_result, process_options, carriers):
        solution_values = linear_programming_result.x

        number_of_process_options = len(process_options)
        raw_purchased_carrier_amounts = solution_values[number_of_process_options:]

        purchased_carrier_amounts = {
            carrier: float(amount) for carrier, amount in zip(carriers, raw_purchased_carrier_amounts, strict=False)
        }
        logging.debug('Carrier amounts: %s', purchased_carrier_amounts)

        return purchased_carrier_amounts
