# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from optimization.optimization_type import OptimizationType


class TestOptimizationType:
    """Test cases for OptimizationType enum."""

    def test_optimization_type_has_all_expected_values(self):
        """Test that OptimizationType has all expected enum values."""
        assert OptimizationType.LINEAR_PROGRAMMING.value == 'LINEAR_PROGRAMMING'
        assert OptimizationType.COMPARING.value == 'COMPARING'
        assert OptimizationType.REGION_MULTI_PERIOD.value == 'REGION_MULTI_PERIOD'
        assert len(list(OptimizationType)) == 3

    def test_from_string_returns_linear_programming(self):
        """Test from_string returns LINEAR_PROGRAMMING."""
        opt_type = OptimizationType.from_string('LINEAR_PROGRAMMING')
        assert opt_type == OptimizationType.LINEAR_PROGRAMMING

    def test_from_string_raises_error_for_unknown_type(self):
        """Test from_string raises ValueError for unknown type."""
        with pytest.raises(ValueError, match='Unknown optimization type: INVALID_TYPE') as exc_info:
            OptimizationType.from_string('INVALID_TYPE')
        assert 'Unknown optimization type: INVALID_TYPE' in str(exc_info.value)

    def test_all_enum_values_parseable(self):
        """Test that all enum values can be parsed back."""
        for opt_type in OptimizationType:
            parsed = OptimizationType.from_string(opt_type.value)
            assert parsed == opt_type

    def test_is_region_scoped_true_for_region_multi_period(self):
        assert OptimizationType.REGION_MULTI_PERIOD.is_region_scoped is True

    def test_is_region_scoped_false_for_non_region_types(self):
        assert OptimizationType.LINEAR_PROGRAMMING.is_region_scoped is False
        assert OptimizationType.COMPARING.is_region_scoped is False

    def test_from_string_parses_region_multi_period(self):
        assert OptimizationType.from_string('REGION_MULTI_PERIOD') == OptimizationType.REGION_MULTI_PERIOD
