# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import MagicMock, patch

import pytest

from optimization.comparing_optimization import ComparingOptimization
from optimization.optimization_context import OptimizationContext


@pytest.fixture
def mock_production_unit():
    """Create mock production unit."""
    return MagicMock()


@pytest.fixture
def mock_result():
    """Create mock optimization result."""
    result = MagicMock()
    result.cost_per_year_in_euro = 1000.0
    result.selected_rolling_planning_horizon_in_years = 5
    return result


@pytest.fixture
def context():
    """Create OptimizationContext with simulation options."""
    simulation_options = {
        'year_increment': 1,
        'rolling_planning_horizon_in_years': 5,
    }
    ctx = OptimizationContext(
        co2_cost_in_euro_per_t_co2=100.0,
        interest_rate=0.05,
        simulation_options=simulation_options,
    )
    return ctx


@pytest.fixture
def optimization(mock_production_unit, context):
    """Create ComparingOptimization instance."""
    return ComparingOptimization(2026, mock_production_unit, context)


class TestComparingOptimizationConstruction:
    """Test ComparingOptimization initialization."""

    def test_construction(self, mock_production_unit, context):
        """Test instance creation."""
        opt = ComparingOptimization(2026, mock_production_unit, context)

        assert opt._year == 2026
        assert opt._production_unit == mock_production_unit
        assert opt._context == context


class TestOptimizeWhenHorizonsEqual:
    """Test optimize when short and long horizons are the same."""

    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_equal_horizons_returns_single_result(self, mock_lp_class, optimization, mock_result):
        """When horizons are equal, should optimize once and return result."""
        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.return_value = mock_result
        mock_lp_class.return_value = mock_lp_instance

        # Set equal horizons
        optimization._context.simulation_options['year_increment'] = 5
        optimization._context.simulation_options['rolling_planning_horizon_in_years'] = 5

        result = optimization.optimize()

        assert result == mock_result
        # Should only call optimize once
        mock_lp_class.assert_called_once()

    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_creates_lp_optimization_with_correct_horizon(self, mock_lp_class, optimization):
        """Verify LP optimization is created with the correct horizon."""
        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.return_value = MagicMock()
        mock_lp_class.return_value = mock_lp_instance

        optimization._context.simulation_options['year_increment'] = 5
        optimization._context.simulation_options['rolling_planning_horizon_in_years'] = 5

        optimization.optimize()

        # Verify LP was created with correct parameters
        assert mock_lp_class.call_count == 1
        call_args = mock_lp_class.call_args
        assert call_args[0][0] == 2026  # year
        assert call_args[0][1] == optimization._production_unit


class TestOptimizeWhenHorizonsDiffer:
    """Test optimize when short and long horizons differ."""

    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_compares_two_horizons(self, mock_lp_class, optimization):
        """When horizons differ, should optimize both and compare."""
        short_result = MagicMock()
        short_result.cost_per_year_in_euro = 1500.0
        short_result.selected_rolling_planning_horizon_in_years = 1

        long_result = MagicMock()
        long_result.cost_per_year_in_euro = 1000.0
        long_result.selected_rolling_planning_horizon_in_years = 5

        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.side_effect = [short_result, long_result]
        mock_lp_class.return_value = mock_lp_instance

        result = optimization.optimize()

        # Should return the better result (lower cost)
        assert result == long_result
        # Should call LP optimization twice
        assert mock_lp_class.call_count == 2

    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_returns_short_horizon_when_cheaper(self, mock_lp_class, optimization):
        """Should return short horizon result when it's cheaper."""
        short_result = MagicMock()
        short_result.cost_per_year_in_euro = 800.0
        short_result.selected_rolling_planning_horizon_in_years = 1

        long_result = MagicMock()
        long_result.cost_per_year_in_euro = 1000.0
        long_result.selected_rolling_planning_horizon_in_years = 5

        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.side_effect = [short_result, long_result]
        mock_lp_class.return_value = mock_lp_instance

        result = optimization.optimize()

        assert result == short_result

    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_returns_long_horizon_when_cheaper(self, mock_lp_class, optimization):
        """Should return long horizon result when it's cheaper."""
        short_result = MagicMock()
        short_result.cost_per_year_in_euro = 1500.0
        short_result.selected_rolling_planning_horizon_in_years = 1

        long_result = MagicMock()
        long_result.cost_per_year_in_euro = 1000.0
        long_result.selected_rolling_planning_horizon_in_years = 5

        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.side_effect = [short_result, long_result]
        mock_lp_class.return_value = mock_lp_instance

        result = optimization.optimize()

        assert result == long_result


class TestContextWithHorizon:
    """Test context creation with modified horizon."""

    def test_creates_new_context_with_modified_horizon(self, optimization):
        """Should create new context with different horizon."""
        new_horizon = 10

        new_context = optimization._context_with_horizon(new_horizon)

        assert new_context.simulation_options['rolling_planning_horizon_in_years'] == new_horizon
        # Original context should be unchanged
        assert optimization._context.simulation_options['rolling_planning_horizon_in_years'] == 5

    def test_preserves_other_simulation_options(self, optimization):
        """Should preserve other simulation options in new context."""
        optimization._context.simulation_options['some_other_option'] = 'value'
        new_horizon = 10

        new_context = optimization._context_with_horizon(new_horizon)

        assert new_context.simulation_options['some_other_option'] == 'value'

    def test_preserves_co2_cost(self, optimization):
        """Should preserve CO2 cost in new context."""
        new_context = optimization._context_with_horizon(10)

        assert new_context.co2_cost_in_euro_per_t_co2 == 100.0

    def test_preserves_interest_rate(self, optimization):
        """Should preserve interest rate in new context."""
        new_context = optimization._context_with_horizon(10)

        assert new_context.interest_rate == 0.05

    def test_preserves_site_attribute(self, optimization):
        """Should copy site attribute if it exists in original context."""
        mock_site = MagicMock()
        optimization._context.site = mock_site

        new_context = optimization._context_with_horizon(10)

        assert new_context.site == mock_site

    def test_handles_missing_site_attribute(self, optimization):
        """Should handle case where context has no site attribute."""
        # Remove site attribute if it exists
        if hasattr(optimization._context, 'site'):
            delattr(optimization._context, 'site')

        new_context = optimization._context_with_horizon(10)

        # Should not have site attribute or should be None
        assert not hasattr(new_context, 'site') or getattr(new_context, 'site', None) is None


class TestBetterResult:
    """Test result comparison logic."""

    def test_returns_first_when_cheaper(self, optimization):
        """Should return first result when it's cheaper."""
        first_result = MagicMock()
        first_result.cost_per_year_in_euro = 800.0
        first_result.selected_rolling_planning_horizon_in_years = 1

        second_result = MagicMock()
        second_result.cost_per_year_in_euro = 1000.0
        second_result.selected_rolling_planning_horizon_in_years = 5

        result = optimization._better_result(first_result, second_result)

        assert result == first_result

    def test_returns_second_when_cheaper(self, optimization):
        """Should return second result when it's cheaper."""
        first_result = MagicMock()
        first_result.cost_per_year_in_euro = 1500.0
        first_result.selected_rolling_planning_horizon_in_years = 1

        second_result = MagicMock()
        second_result.cost_per_year_in_euro = 1000.0
        second_result.selected_rolling_planning_horizon_in_years = 5

        result = optimization._better_result(first_result, second_result)

        assert result == second_result

    def test_returns_first_when_costs_equal_first_horizon_longer(self, optimization):
        """When costs equal, should return first result if its horizon is >= second."""
        first_result = MagicMock()
        first_result.cost_per_year_in_euro = 1000.0
        first_result.selected_rolling_planning_horizon_in_years = 5

        second_result = MagicMock()
        second_result.cost_per_year_in_euro = 1000.0
        second_result.selected_rolling_planning_horizon_in_years = 3

        result = optimization._better_result(first_result, second_result)

        assert result == first_result

    def test_returns_second_when_costs_equal_second_horizon_longer(self, optimization):
        """When costs equal, should return second result if its horizon is > first."""
        first_result = MagicMock()
        first_result.cost_per_year_in_euro = 1000.0
        first_result.selected_rolling_planning_horizon_in_years = 3

        second_result = MagicMock()
        second_result.cost_per_year_in_euro = 1000.0
        second_result.selected_rolling_planning_horizon_in_years = 5

        result = optimization._better_result(first_result, second_result)

        assert result == second_result

    def test_returns_first_when_costs_and_horizons_equal(self, optimization):
        """When costs and horizons equal, should return first result."""
        first_result = MagicMock()
        first_result.cost_per_year_in_euro = 1000.0
        first_result.selected_rolling_planning_horizon_in_years = 5

        second_result = MagicMock()
        second_result.cost_per_year_in_euro = 1000.0
        second_result.selected_rolling_planning_horizon_in_years = 5

        result = optimization._better_result(first_result, second_result)

        assert result == first_result


class TestLoggingBehavior:
    """Test logging of optimization decisions."""

    @patch('optimization.comparing_optimization.logger')
    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_logs_short_and_long_term_costs(self, mock_lp_class, mock_logger, optimization):
        """Should log both short and long term costs."""
        short_result = MagicMock()
        short_result.cost_per_year_in_euro = 1500.0
        short_result.selected_rolling_planning_horizon_in_years = 1

        long_result = MagicMock()
        long_result.cost_per_year_in_euro = 1000.0
        long_result.selected_rolling_planning_horizon_in_years = 5

        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.side_effect = [short_result, long_result]
        mock_lp_class.return_value = mock_lp_instance

        optimization.optimize()

        # Verify logging calls
        assert mock_logger.info.call_count >= 3  # Short term cost, Long term cost, decision
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any('Short term' in call for call in calls)
        assert any('Long term' in call for call in calls)

    @patch('optimization.comparing_optimization.logger')
    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_logs_short_term_choice_decision(self, mock_lp_class, mock_logger, optimization):
        """Should log when short term horizon is chosen."""
        short_result = MagicMock()
        short_result.cost_per_year_in_euro = 800.0
        short_result.selected_rolling_planning_horizon_in_years = 1

        long_result = MagicMock()
        long_result.cost_per_year_in_euro = 1000.0
        long_result.selected_rolling_planning_horizon_in_years = 5

        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.side_effect = [short_result, long_result]
        mock_lp_class.return_value = mock_lp_instance

        optimization.optimize()

        # Check that short term choice is logged
        calls_str = ' '.join(str(call) for call in mock_logger.info.call_args_list)
        assert 'Short term' in calls_str

    @patch('optimization.comparing_optimization.logger')
    @patch('optimization.comparing_optimization.LinearProgrammingOptimization')
    def test_logs_long_term_choice_decision(self, mock_lp_class, mock_logger, optimization):
        """Should log when long term horizon is chosen."""
        short_result = MagicMock()
        short_result.cost_per_year_in_euro = 1500.0
        short_result.selected_rolling_planning_horizon_in_years = 1

        long_result = MagicMock()
        long_result.cost_per_year_in_euro = 1000.0
        long_result.selected_rolling_planning_horizon_in_years = 5

        mock_lp_instance = MagicMock()
        mock_lp_instance.optimize.side_effect = [short_result, long_result]
        mock_lp_class.return_value = mock_lp_instance

        optimization.optimize()

        # Check that long term choice is logged
        calls_str = ' '.join(str(call) for call in mock_logger.info.call_args_list)
        assert 'Long term' in calls_str
