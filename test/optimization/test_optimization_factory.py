# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for OptimizationFactory class."""

import unittest
from unittest import mock

import pytest

from optimization.optimization_factory import OptimizationFactory
from optimization.optimization_type import OptimizationType


class TestOptimizationFactoryInit(unittest.TestCase):
    """Tests for OptimizationFactory initialization."""

    def test_init_with_linear_programming_type(self):
        """Test initialization with LP optimization type."""
        factory = OptimizationFactory(OptimizationType.LINEAR_PROGRAMMING)
        assert factory._type == OptimizationType.LINEAR_PROGRAMMING

    def test_init_with_comparing_type(self):
        """Test initialization with Comparing optimization type."""
        factory = OptimizationFactory(OptimizationType.COMPARING)
        assert factory._type == OptimizationType.COMPARING

    def test_init_with_region_multi_period_type(self):
        """Test initialization with Region Multi-Period optimization type."""
        factory = OptimizationFactory(OptimizationType.REGION_MULTI_PERIOD)
        assert factory._type == OptimizationType.REGION_MULTI_PERIOD


class TestOptimizationFactoryCreateValidation(unittest.TestCase):
    """Tests for type validation in create method."""

    def test_create_rejects_unknown_type(self):
        """Test that create rejects unknown optimization type."""
        factory = OptimizationFactory('UNKNOWN_TYPE')
        mock_context = mock.MagicMock()

        with pytest.raises(ValueError, match='Unknown optimization type'):
            factory.create(2020, mock.MagicMock(), mock_context)

    def test_create_rejects_none_type(self):
        """Test that create rejects None optimization type."""
        factory = OptimizationFactory(None)
        mock_context = mock.MagicMock()

        with pytest.raises(ValueError, match='Unknown optimization type'):
            factory.create(2020, mock.MagicMock(), mock_context)


class TestOptimizationFactoryRegionScoped(unittest.TestCase):
    """Tests for region-scoped type rejection."""

    def test_create_rejects_region_scoped_types(self):
        """Test that region-scoped types are rejected for per-PU optimization."""
        # Create a mock OptimizationType that is region-scoped
        mock_type = mock.MagicMock(spec=OptimizationType)
        mock_type.is_region_scoped = True
        mock_type.__str__ = lambda self: 'REGION_SCOPED_TYPE'

        factory = OptimizationFactory(mock_type)
        mock_context = mock.MagicMock()

        with pytest.raises(ValueError, match='region-scoped dispatch'):
            factory.create(2020, mock.MagicMock(), mock_context)


class TestOptimizationFactoryCreateLinearProgramming(unittest.TestCase):
    """Tests for creating LinearProgrammingOptimization."""

    def test_create_linear_programming_optimization(self):
        """Test creating LP optimization."""
        factory = OptimizationFactory(OptimizationType.LINEAR_PROGRAMMING)
        mock_pu = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {}

        with mock.patch('optimization.optimization_factory.LinearProgrammingOptimization') as mock_lp_class:
            factory.create(2020, mock_pu, mock_context)
            mock_lp_class.assert_called_once_with(2020, mock_pu, mock_context)

    def test_create_linear_programming_year_passed(self):
        """Test that year is passed correctly to LP optimization."""
        factory = OptimizationFactory(OptimizationType.LINEAR_PROGRAMMING)
        mock_pu = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {}

        with mock.patch('optimization.optimization_factory.LinearProgrammingOptimization') as mock_lp_class:
            factory.create(2025, mock_pu, mock_context)
            args = mock_lp_class.call_args[0]
            assert args[0] == 2025


class TestOptimizationFactoryCreateComparing(unittest.TestCase):
    """Tests for creating ComparingOptimization."""

    def test_create_comparing_optimization(self):
        """Test creating Comparing optimization."""
        factory = OptimizationFactory(OptimizationType.COMPARING)
        mock_pu = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {}

        with mock.patch('optimization.optimization_factory.ComparingOptimization') as mock_comparing_class:
            factory.create(2020, mock_pu, mock_context)
            mock_comparing_class.assert_called_once_with(2020, mock_pu, mock_context)


class TestOptimizationFactoryEmissionBudgetValidation(unittest.TestCase):
    """Tests for emission budget validation."""

    def test_emission_budget_rejected_for_comparing(self):
        """Test that emission budget is rejected for Comparing."""
        factory = OptimizationFactory(OptimizationType.COMPARING)
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {'overall_emission_budget_in_t_co2': 750.0}

        with pytest.raises(ValueError, match='only supported for REGION_MULTI_PERIOD'):
            factory._validate_supported_simulation_options(mock_context)

    def test_emission_budget_allowed_for_region_multi_period(self):
        """Test that emission budget is allowed for REGION_MULTI_PERIOD."""
        factory = OptimizationFactory(OptimizationType.REGION_MULTI_PERIOD)
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {'overall_emission_budget_in_t_co2': 1000.0}

        # Just validate emission budget separately
        factory._validate_supported_simulation_options(mock_context)
        # Should not raise

    def test_emission_budget_rejected_for_linear_programming(self):
        """Test that emission budget is rejected for LP."""
        factory = OptimizationFactory(OptimizationType.LINEAR_PROGRAMMING)
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {'overall_emission_budget_in_t_co2': 1000.0}

        with pytest.raises(ValueError, match='only supported for REGION_MULTI_PERIOD'):
            factory._validate_supported_simulation_options(mock_context)

    def test_no_emission_budget_allowed_all_types(self):
        """Test that absence of emission budget is allowed for all types."""
        for opt_type in [
            OptimizationType.LINEAR_PROGRAMMING,
            OptimizationType.COMPARING,
        ]:
            factory = OptimizationFactory(opt_type)
            mock_context = mock.MagicMock()
            mock_context.simulation_options = {}

            # Should not raise
            factory._validate_supported_simulation_options(mock_context)

    def test_emission_budget_none_allowed_all_types(self):
        """Test that emission budget=None is allowed for all types."""
        for opt_type in [
            OptimizationType.LINEAR_PROGRAMMING,
            OptimizationType.COMPARING,
        ]:
            factory = OptimizationFactory(opt_type)
            mock_context = mock.MagicMock()
            mock_context.simulation_options = {'overall_emission_budget_in_t_co2': None}

            # Should not raise
            factory._validate_supported_simulation_options(mock_context)


class TestOptimizationFactoryValidationOrder(unittest.TestCase):
    """Tests for validation order in create method."""

    def test_type_validation_before_region_scoped_check(self):
        """Test that type validation happens before region-scoped check."""
        factory = OptimizationFactory('INVALID')
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {}

        # Should fail on unknown type, not on region-scoped check
        with pytest.raises(ValueError, match='Unknown optimization type'):
            factory.create(2020, mock.MagicMock(), mock_context)

    def test_region_scoped_check_before_emission_budget(self):
        """Test that region-scoped check happens before emission budget validation."""
        mock_type = mock.MagicMock(spec=OptimizationType)
        mock_type.is_region_scoped = True
        mock_type.__str__ = lambda self: 'REGION_SCOPED'

        factory = OptimizationFactory(mock_type)
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {'overall_emission_budget_in_t_co2': 1000.0}

        # Should fail on region-scoped, not emission budget
        with pytest.raises(ValueError, match='region-scoped dispatch'):
            factory.create(2020, mock.MagicMock(), mock_context)


class TestOptimizationFactoryProductionUnitHandling(unittest.TestCase):
    """Tests for production unit handling."""

    def test_production_unit_passed_to_optimization(self):
        """Test that production unit is passed correctly."""
        factory = OptimizationFactory(OptimizationType.LINEAR_PROGRAMMING)
        mock_pu = mock.MagicMock()
        mock_pu.id = 'test_pu_123'
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {}

        with mock.patch('optimization.optimization_factory.LinearProgrammingOptimization') as mock_lp_class:
            factory.create(2020, mock_pu, mock_context)
            args = mock_lp_class.call_args[0]
            assert args[1] == mock_pu

    def test_context_passed_to_optimization(self):
        """Test that context is passed correctly."""
        factory = OptimizationFactory(OptimizationType.COMPARING)
        mock_pu = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {}

        with mock.patch('optimization.optimization_factory.ComparingOptimization') as mock_comparing_class:
            factory.create(2020, mock_pu, mock_context)
            args = mock_comparing_class.call_args[0]
            assert args[2] == mock_context


class TestOptimizationFactoryFallbackError(unittest.TestCase):
    """Tests for fallback error handling (unreachable code coverage)."""

    def test_create_fallback_error_for_unhandled_type(self):
        """Test fallback error for OptimizationType that passes isinstance but isn't handled (lines 36-37)."""
        # Create a mock OptimizationType that isn't one of the handled types
        mock_type = mock.MagicMock(spec=OptimizationType)
        mock_type.is_region_scoped = False  # Not region-scoped so it passes check
        # Don't set __eq__ to match any of the known types
        mock_type.__eq__ = lambda self, other: False
        mock_type.__str__ = lambda self: 'UNKNOWN_SUBTYPE'

        factory = OptimizationFactory(mock_type)
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {}

        with pytest.raises(ValueError, match='Unknown optimization type'):
            factory.create(2020, mock.MagicMock(), mock_context)


if __name__ == '__main__':
    unittest.main()
