# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for MultiPeriodOptimizationResult class."""

import unittest
from unittest import mock

import numpy as np
import pytest

from optimization.multi_period_optimization_result import MultiPeriodOptimizationResult


class TestMultiPeriodOptimizationResultInitialization(unittest.TestCase):
    """Tests for MultiPeriodOptimizationResult initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_process_option_1 = mock.MagicMock()
        self.mock_process_option_2 = mock.MagicMock()
        self.mock_carrier_1 = mock.MagicMock()
        self.mock_carrier_2 = mock.MagicMock()
        self.simulation_periods = [2020, 2025]

    def _create_lp_result(self, num_process_options=2, num_carriers=2, num_periods=2):
        """Create a mock LP result with solution values."""
        variables_per_period = num_process_options + num_carriers
        total_variables = num_periods * variables_per_period + num_periods * num_process_options

        # Create solution vector with realistic values
        solution = np.zeros(total_variables)

        # Fill in execution counts and purchased amounts for each period
        for period_idx in range(num_periods):
            # Execution counts (process options)
            exec_start = period_idx * variables_per_period
            exec_end = exec_start + num_process_options
            solution[exec_start:exec_end] = [10.0, 20.0][:num_process_options]

            # Purchased carrier amounts
            carrier_start = exec_end
            carrier_end = carrier_start + num_carriers
            solution[carrier_start:carrier_end] = [100.0, 200.0][:num_carriers]

        # Fill in new capacity counts
        new_capacity_offset = num_periods * variables_per_period
        for period_idx in range(num_periods):
            new_capacity_start = new_capacity_offset + period_idx * num_process_options
            new_capacity_end = new_capacity_start + num_process_options
            solution[new_capacity_start:new_capacity_end] = [5.0, 10.0][:num_process_options]

        mock_result = mock.MagicMock()
        mock_result.x = solution
        return mock_result

    def test_initialization_with_basic_parameters(self):
        """Test initialization with basic parameters."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        assert result.simulation_periods == self.simulation_periods
        assert result.total_cost_in_euro is None
        assert result.interest_rate is None

    def test_initialization_with_total_cost(self):
        """Test initialization with total cost."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]
        total_cost = 1000.5

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
            total_cost_in_euro=total_cost,
        )

        assert result.total_cost_in_euro == total_cost

    def test_initialization_with_interest_rate(self):
        """Test initialization with interest rate."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]
        interest_rate = 0.05

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
            interest_rate=interest_rate,
        )

        assert result.interest_rate == interest_rate

    def test_initialization_with_emission_budget(self):
        """Test initialization with emission budget."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]
        budget_used = 500.0
        budget_available = 1000.0

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
            overall_emission_budget_used_in_t_co2=budget_used,
            overall_emission_budget_in_t_co2=budget_available,
        )

        assert result.overall_emission_budget_used_in_t_co2 == budget_used
        assert result.overall_emission_budget_in_t_co2 == budget_available


class TestMultiPeriodOptimizationResultResults(unittest.TestCase):
    """Tests for accessing results by year."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_process_option_1 = mock.MagicMock()
        self.mock_process_option_2 = mock.MagicMock()
        self.mock_carrier_1 = mock.MagicMock()
        self.mock_carrier_2 = mock.MagicMock()
        self.simulation_periods = [2020, 2025]

    def _create_lp_result(self, num_process_options=2, num_carriers=2, num_periods=2):
        """Create a mock LP result with solution values."""
        variables_per_period = num_process_options + num_carriers
        total_variables = num_periods * variables_per_period + num_periods * num_process_options

        solution = np.zeros(total_variables)

        for period_idx in range(num_periods):
            exec_start = period_idx * variables_per_period
            exec_end = exec_start + num_process_options
            solution[exec_start:exec_end] = [10.0, 20.0][:num_process_options]

            carrier_start = exec_end
            carrier_end = carrier_start + num_carriers
            solution[carrier_start:carrier_end] = [100.0, 200.0][:num_carriers]

        new_capacity_offset = num_periods * variables_per_period
        for period_idx in range(num_periods):
            new_capacity_start = new_capacity_offset + period_idx * num_process_options
            new_capacity_end = new_capacity_start + num_process_options
            solution[new_capacity_start:new_capacity_end] = [5.0, 10.0][:num_process_options]

        mock_result = mock.MagicMock()
        mock_result.x = solution
        return mock_result

    def test_has_result_for_year_existing_year(self):
        """Test has_result_for_year returns True for existing year."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        assert result.has_result_for_year(2020)
        assert result.has_result_for_year(2025)

    def test_has_result_for_year_non_existing_year(self):
        """Test has_result_for_year returns False for non-existing year."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        assert not result.has_result_for_year(2030)

    def test_get_result_for_year_existing_year(self):
        """Test get_result_for_year returns result for existing year."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        year_result = result.get_result_for_year(2020)
        assert year_result is not None
        assert self.mock_process_option_1 in year_result.process_execution_counts
        assert self.mock_carrier_1 in year_result.purchased_carrier_amounts

    def test_get_result_for_year_non_existing_year_raises_error(self):
        """Test get_result_for_year raises ValueError for non-existing year."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        with pytest.raises(ValueError, match='No multi-period result for year 2030'):
            result.get_result_for_year(2030)

    def test_get_new_capacity_for_year_existing_year(self):
        """Test get_new_capacity_for_year returns capacity for existing year."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        capacity = result.get_new_capacity_for_year(2020)
        assert capacity is not None
        assert self.mock_process_option_1 in capacity
        assert self.mock_process_option_2 in capacity

    def test_get_new_capacity_for_year_non_existing_year_raises_error(self):
        """Test get_new_capacity_for_year raises ValueError for non-existing year."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        with pytest.raises(ValueError, match='No multi-period new-capacity result for year 2030'):
            result.get_new_capacity_for_year(2030)


class TestMultiPeriodOptimizationResultProperties(unittest.TestCase):
    """Tests for properties."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_process_option_1 = mock.MagicMock()
        self.mock_process_option_2 = mock.MagicMock()
        self.mock_carrier_1 = mock.MagicMock()
        self.mock_carrier_2 = mock.MagicMock()
        self.simulation_periods = [2020, 2025]

    def _create_lp_result(self, num_process_options=2, num_carriers=2, num_periods=2):
        """Create a mock LP result with solution values."""
        variables_per_period = num_process_options + num_carriers
        total_variables = num_periods * variables_per_period + num_periods * num_process_options

        solution = np.zeros(total_variables)

        for period_idx in range(num_periods):
            exec_start = period_idx * variables_per_period
            exec_end = exec_start + num_process_options
            solution[exec_start:exec_end] = [10.0, 20.0][:num_process_options]

            carrier_start = exec_end
            carrier_end = carrier_start + num_carriers
            solution[carrier_start:carrier_end] = [100.0, 200.0][:num_carriers]

        new_capacity_offset = num_periods * variables_per_period
        for period_idx in range(num_periods):
            new_capacity_start = new_capacity_offset + period_idx * num_process_options
            new_capacity_end = new_capacity_start + num_process_options
            solution[new_capacity_start:new_capacity_end] = [5.0, 10.0][:num_process_options]

        mock_result = mock.MagicMock()
        mock_result.x = solution
        return mock_result

    def test_simulation_periods_property(self):
        """Test simulation_periods property returns copy of periods."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        periods = result.simulation_periods
        assert periods == self.simulation_periods
        # Verify it's a copy, not the same object
        assert periods is not self.simulation_periods

    def test_overall_emission_budget_summary_with_budget(self):
        """Test overall_emission_budget_summary returns dict when budget is set."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]
        budget_used = 500.0
        budget_available = 1000.0

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
            overall_emission_budget_used_in_t_co2=budget_used,
            overall_emission_budget_in_t_co2=budget_available,
        )

        summary = result.overall_emission_budget_summary
        assert summary is not None
        assert summary['used_in_t_co2'] == budget_used
        assert summary['available_in_t_co2'] == budget_available

    def test_overall_emission_budget_summary_without_budget(self):
        """Test overall_emission_budget_summary returns None when budget is not set."""
        lp_result = self._create_lp_result()
        process_options = [self.mock_process_option_1, self.mock_process_option_2]
        carriers = [self.mock_carrier_1, self.mock_carrier_2]

        result = MultiPeriodOptimizationResult(
            lp_result,
            process_options,
            carriers,
            self.simulation_periods,
        )

        summary = result.overall_emission_budget_summary
        assert summary is None
