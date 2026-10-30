# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from optimization.carrier_netto_amount_calculator import CarrierNettoAmountCalculator
from optimization.optimization_result import OptimizationResult


class MultiPeriodOptimizationResult:
    def __init__(
        self,
        linear_programming_result,
        process_options,
        carriers,
        simulation_periods,
        total_cost_in_euro=None,
        interest_rate=None,
        overall_emission_budget_used_in_t_co2=None,
        overall_emission_budget_in_t_co2=None,
    ):
        self._process_options = list(process_options)
        self._carriers = list(carriers)
        self._simulation_periods = list(simulation_periods)
        self.total_cost_in_euro = self._normalized_total_cost(total_cost_in_euro)
        self.interest_rate = self._normalized_interest_rate(interest_rate)
        self.overall_emission_budget_used_in_t_co2 = self._normalized_optional_float(overall_emission_budget_used_in_t_co2)
        self.overall_emission_budget_in_t_co2 = self._normalized_optional_float(overall_emission_budget_in_t_co2)

        solution_values = linear_programming_result.x
        number_of_process_options = len(self._process_options)
        number_of_carriers = len(self._carriers)
        number_of_periods = len(self._simulation_periods)
        variables_per_period = number_of_process_options + number_of_carriers
        new_capacity_offset = number_of_periods * variables_per_period

        self._results_by_year = {}
        self._new_capacity_by_year = {}

        for period_index, year in enumerate(self._simulation_periods):
            exec_start = period_index * variables_per_period
            exec_end = exec_start + number_of_process_options
            raw_process_execution_counts = solution_values[exec_start:exec_end]
            process_execution_counts = {
                process_option: float(count)
                for process_option, count in zip(
                    self._process_options,
                    raw_process_execution_counts,
                    strict=False,
                )
            }

            carrier_start = exec_end
            carrier_end = carrier_start + number_of_carriers
            raw_purchased_carrier_amounts = solution_values[carrier_start:carrier_end]
            purchased_carrier_amounts = {
                carrier: float(amount)
                for carrier, amount in zip(
                    self._carriers,
                    raw_purchased_carrier_amounts,
                    strict=False,
                )
            }

            new_capacity_start = new_capacity_offset + period_index * number_of_process_options
            new_capacity_end = new_capacity_start + number_of_process_options
            raw_new_capacity = solution_values[new_capacity_start:new_capacity_end]
            new_capacity_counts = {
                process_option: float(capacity)
                for process_option, capacity in zip(
                    self._process_options,
                    raw_new_capacity,
                    strict=False,
                )
            }

            carrier_netto_amounts = CarrierNettoAmountCalculator().calculate(process_execution_counts, self._carriers, year)

            period_result = OptimizationResult(
                process_execution_counts,
                purchased_carrier_amounts,
                total_cost_in_euro=None,
                modeled_year_count=None,
                selected_rolling_planning_horizon_in_years=None,
                interest_rate=self.interest_rate,
                carrier_netto_amounts=carrier_netto_amounts,
            )

            self._results_by_year[year] = period_result
            self._new_capacity_by_year[year] = new_capacity_counts

            logging.debug(
                'Multi-period optimization result for year %s: exec=%s, new_capacity=%s',
                year,
                process_execution_counts,
                new_capacity_counts,
            )

    @staticmethod
    def _normalized_total_cost(total_cost_in_euro):
        if total_cost_in_euro is None:
            return None
        return float(total_cost_in_euro)

    @staticmethod
    def _normalized_interest_rate(interest_rate):
        if interest_rate is None:
            return None
        return float(interest_rate)

    @staticmethod
    def _normalized_optional_float(value):
        if value is None:
            return None
        return float(value)

    def has_result_for_year(self, year):
        return year in self._results_by_year

    def get_result_for_year(self, year):
        if year not in self._results_by_year:
            message = f'No multi-period result for year {year}. Available years: {self.simulation_periods}'
            raise ValueError(message)
        return self._results_by_year[year]

    def get_new_capacity_for_year(self, year):
        if year not in self._new_capacity_by_year:
            message = f'No multi-period new-capacity result for year {year}. Available years: {self.simulation_periods}'
            raise ValueError(message)
        return self._new_capacity_by_year[year]

    @property
    def simulation_periods(self):
        return list(self._simulation_periods)

    @property
    def overall_emission_budget_summary(self):
        if self.overall_emission_budget_in_t_co2 is None:
            return None

        return {
            'used_in_t_co2': self.overall_emission_budget_used_in_t_co2,
            'available_in_t_co2': self.overall_emission_budget_in_t_co2,
        }
