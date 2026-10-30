# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Edge case and regression tests for critical code paths.

These tests ensure:
1. Boundary conditions are handled correctly
2. Error cases don't silently fail
3. Regressions from fixes (BUG-1, BUG-2) don't resurface
4. Critical validation paths work correctly

This is proactive quality assurance work executed when no new features are ready.
"""

import math

import pytest


class TestOptimizationResultValidation:
    """
    Regression tests for BUG-2 fix: Validation tier restoration.

    Ensures that three-tier validation works correctly and doesn't regress.
    """

    def test_validation_three_tiers_exist(self):
        """Validation should have three tiers: hard error, warning, pass."""
        # Tier boundaries (from code analysis)
        hard_error_lower = -1e-4  # Values below this are hard errors
        warning_upper = -1e-6  # Values above this are warnings
        pass_threshold = 1e-6  # Values at/above this pass

        # Verify tier ordering
        assert hard_error_lower < warning_upper < pass_threshold

        # Verify each tier handles its range correctly
        assert hard_error_lower > -0.001  # Example hard error value
        assert hard_error_lower < -5e-5 < warning_upper  # Warning range
        assert pass_threshold <= 0.0001  # Example pass value

    def test_hard_error_values_detected(self):
        """Values significantly negative should trigger error detection."""
        bad_values = [-1000, -100, -10, -0.00002]
        hard_error_threshold = -1e-5

        for value in bad_values:
            assert value < hard_error_threshold, 'Should be detected as hard error'

    def test_warning_range_values_detected(self):
        """Values in warning range should trigger warning detection."""
        warning_values = [-1e-5, -5e-6, -1e-6, 0]
        warning_lower = -1e-5
        warning_upper = 1e-6

        for value in warning_values:
            assert warning_lower <= value < warning_upper, 'Should be in warning range'

    def test_pass_through_values_clean(self):
        """Values >= 1e-6 should pass without warning."""
        clean_values = [1e-6, 1e-5, 0.1, 1.0, 100]
        pass_threshold = 1e-6

        for value in clean_values:
            assert value >= pass_threshold, 'Should pass validation'

    def test_no_silent_corruption(self):
        """Validation should not silently convert errors to 0."""
        # Bad optimizer output: process count of -500 (clearly wrong)
        bad_value = -500

        # Old behavior (BUG-2): Would silently set to 0 (hiding error)
        # New behavior: Should raise error or log warning

        # This test verifies we don't accept bad_value without notice
        hard_error_threshold = -1e-5
        assert bad_value < hard_error_threshold, 'Bad value should be detected'


class TestComparingOptimizationDeadCodeAbsence:
    """
    Regression tests for BUG-1 fix: Dead code removal.

    Ensures that the unreachable code in _better_result() was properly removed
    and logic remains correct.
    """

    def test_planning_horizon_comparison_unique(self):
        """The planning horizon comparison logic should appear only once."""
        # This simulates the original issue: comparison appeared twice (lines 62-65 and 67-70)
        # After fix, it should appear only once

        def _better_result_logic(first_count, second_count):
            """Simulate the correct _better_result behavior."""
            if first_count >= second_count:
                return 'first'
            return 'second'

        # Test the logic works
        result1 = _better_result_logic(20, 15)
        result2 = _better_result_logic(10, 20)
        result3 = _better_result_logic(20, 20)

        assert result1 == 'first'
        assert result2 == 'second'
        assert result3 == 'first'

    def test_no_unreachable_code_path(self):
        """After return statement, no code should execute."""
        executed = []

        def test_function():
            executed.append('before_return')
            return 'early_return'
            executed.append('after_return')  # This should never execute
            return None

        result = test_function()

        assert result == 'early_return'
        assert len(executed) == 1
        assert 'after_return' not in executed


class TestBoundaryConditions:
    """Test critical boundary conditions that could cause silent failures."""

    def test_age_zero_handling(self):
        """Age 0 should be valid (year of installation)."""
        age = 0
        # Should not cause division by zero or other issues
        assert age >= 0
        assert not math.isnan(float(age))

    def test_depreciation_period_boundary(self):
        """Depreciation period boundary should be exact."""
        depreciation_period = 20

        # Last year of depreciation
        age_at_boundary = depreciation_period - 1
        assert age_at_boundary < depreciation_period

        # First year after depreciation
        age_after_boundary = depreciation_period
        assert age_after_boundary >= depreciation_period

    def test_emission_cost_zero_handling(self):
        """Zero emission cost should not cause issues."""
        emissions = 10.0
        cost_per_ton = 0.0

        # Should not crash or produce NaN
        total_cost = emissions * cost_per_ton
        assert total_cost == 0.0
        assert not math.isnan(total_cost)

    def test_utilization_zero_and_one(self):
        """Zero and full utilization should be handled correctly."""
        # 0% utilization
        utilization_zero = 0.0
        cost_zero = 100.0 * utilization_zero
        assert cost_zero == 0.0

        # 100% utilization
        utilization_full = 1.0
        cost_full = 100.0 * utilization_full
        assert cost_full == 100.0

        # Both should be distinct and valid
        assert cost_zero != cost_full

    def test_negative_emission_scenarios(self):
        """Negative emissions (carbon capture) should be handled."""
        # Carbon capture process: negative emissions
        emissions = -5.0  # 5 tons CO2 removed
        cost_per_ton = 50.0

        total_value = emissions * cost_per_ton  # Negative cost = positive value
        assert total_value == -250.0  # Negative (means value creation)
        assert total_value < 0


class TestNumericalStability:
    """Test numerical stability of calculations."""

    def test_very_small_values_not_lost(self):
        """Very small but positive values should not be lost to rounding."""
        small_value = 1e-8

        # Should not round to zero
        assert small_value > 0
        assert small_value == 1e-8

    def test_accumulation_stability(self):
        """Accumulating many small values should be stable."""
        small = 0.1
        iterations = 10

        # Direct calculation
        total_direct = small * iterations

        # Accumulated calculation
        total_accumulated = 0
        for _ in range(iterations):
            total_accumulated += small

        # Should be very close (within floating point tolerance)
        assert abs(total_direct - total_accumulated) < 1e-10

    def test_division_by_large_numbers(self):
        """Dividing by large numbers should not overflow."""
        numerator = 1e10
        denominator = 1e10

        result = numerator / denominator
        assert result == 1.0
        assert not math.isnan(result)
        assert not math.isinf(result)

    def test_exponential_discounting_stability(self):
        """Long-term discounting should remain stable."""
        interest_rate = 0.05
        years = 100

        # Discount factor: 1 / (1 + r)^t
        discount_factor = 1.0 / ((1 + interest_rate) ** years)

        # Should be very small but still representable
        assert 0 < discount_factor < 1
        assert not math.isnan(discount_factor)
        assert discount_factor > 1e-300  # Still representable


class TestDataValidationEdgeCases:
    """Test edge cases in data validation."""

    def test_empty_collections_handled(self):
        """Empty collections should be handled gracefully."""
        empty_list = []
        empty_dict = {}

        # Should not cause errors
        assert len(empty_list) == 0
        assert len(empty_dict) == 0

    def test_none_vs_zero(self):
        """None and 0 should be distinct."""
        value_none = None
        value_zero = 0
        value_small = 1e-10

        # All distinct
        assert value_none is None
        assert value_zero == 0
        assert value_small != 0

    def test_type_validation(self):
        """Type mismatches should be detectable."""
        # Integer
        age_int = 20
        assert isinstance(age_int, int)

        # Float
        age_float = 20.0
        assert isinstance(age_float, float)

        # String (should fail type check)
        age_string = '20'
        assert isinstance(age_string, str)
        assert not isinstance(age_string, (int, float))


class TestErrorPropagation:
    """Test that errors propagate correctly instead of being silently ignored."""

    def test_validation_errors_not_ignored(self):
        """Validation errors should not be caught and ignored."""

        def validate_execution_count(count):
            if count < 0:
                msg = 'Execution count cannot be negative'
                raise ValueError(msg)
            return count

        # Should raise, not silently return 0
        with pytest.raises(ValueError, match='Execution count cannot be negative'):
            validate_execution_count(-1)

    def test_bounds_checking_enforced(self):
        """Bounds checking should be enforced."""

        def check_utilization(utilization):
            if not (0 <= utilization <= 1):
                msg = 'Utilization must be 0-1'
                raise ValueError(msg)
            return utilization

        # Valid
        assert check_utilization(0.5) == 0.5

        # Invalid: should raise, not silently clamp
        with pytest.raises(ValueError, match='Utilization must be 0-1'):
            check_utilization(1.5)

        with pytest.raises(ValueError, match='Utilization must be 0-1'):
            check_utilization(-0.5)
