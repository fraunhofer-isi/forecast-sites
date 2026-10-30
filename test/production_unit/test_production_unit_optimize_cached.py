# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.optimize method with cached and multi-period results."""

import unittest
from unittest import mock

import pytest

from optimization.multi_period_optimization_result import MultiPeriodOptimizationResult
from production_unit.production_unit import ProductionUnit


class TestProductionUnitOptimizeCachedResult(unittest.TestCase):
    """Test ProductionUnit.optimize with cached multi-period result."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_site = mock.MagicMock()
        self.mock_sub_pu_factory = mock.MagicMock()
        self.mock_sub_pu_factory.create_for_start_year.return_value = []
        self.mock_optimization_factory = mock.MagicMock()
        self.mock_process_map = {}
        self.mock_carriers = {}
        self.mock_simulation_options = {
            'rolling_planning_horizon_in_years': 5,
            'start_year': 2020,
        }
        self.mock_minimum_export_data = {}

        self.pu = ProductionUnit(
            id_production_unit=1,
            site=self.mock_site,
            sector='steel',
            minimum_export_interpolation_data_in_t=self.mock_minimum_export_data,
            sub_production_unit_factory=self.mock_sub_pu_factory,
            optimization_factory=self.mock_optimization_factory,
            process_map=self.mock_process_map,
            carriers=self.mock_carriers,
            simulation_options=self.mock_simulation_options,
        )

    def test_optimize_uses_cached_result_when_available(self):
        """Test optimize uses cached multi-period result when available."""
        # Setup: Create a cached multi-period result
        mock_cached_result = mock.MagicMock(spec=MultiPeriodOptimizationResult)
        mock_cached_result.has_result_for_year.return_value = True
        mock_optimization_result = mock.MagicMock()
        mock_cached_result.get_result_for_year.return_value = mock_optimization_result

        # Store the cached result
        self.pu._multi_period_result = mock_cached_result

        # Mock the apply method
        self.pu._apply_multi_period_results = mock.MagicMock()

        # Execute
        mock_context = mock.MagicMock()
        self.pu.optimize(2021, mock_context)

        # Verify: Cached result was used
        assert self.pu.optimization_results == mock_optimization_result
        self.pu._apply_multi_period_results.assert_called_once_with(2021, mock_context)
        # Verify: No new optimization was created
        self.mock_optimization_factory.create.assert_not_called()

    def test_optimize_stores_multi_period_result(self):
        """Test optimize stores multi-period result in cache."""
        # Setup: Create a multi-period optimization result
        mock_multi_period_result = mock.MagicMock(spec=MultiPeriodOptimizationResult)
        mock_optimization_result_for_year = mock.MagicMock()
        mock_multi_period_result.get_result_for_year.return_value = mock_optimization_result_for_year

        # Setup: Mock optimization factory
        mock_optimization = mock.MagicMock()
        mock_optimization.optimize.return_value = mock_multi_period_result
        self.mock_optimization_factory.create.return_value = mock_optimization

        # Mock the apply method
        self.pu._apply_multi_period_results = mock.MagicMock()

        # Execute
        mock_context = mock.MagicMock()
        self.pu.optimize(2020, mock_context)

        # Verify: Multi-period result was stored in cache
        assert self.pu._multi_period_result is mock_multi_period_result
        # Verify: Result for year was set
        assert self.pu.optimization_results == mock_optimization_result_for_year
        # Verify: Apply multi-period results was called
        self.pu._apply_multi_period_results.assert_called_once_with(2020, mock_context)

    def test_optimize_raises_error_when_cached_result_is_none(self):
        """Test optimize raises RuntimeError when _has_cached_multi_period_result is True but _multi_period_result is None."""
        # Setup: Mock _has_cached_multi_period_result to return True
        self.pu._has_cached_multi_period_result = mock.MagicMock(return_value=True)
        # But _multi_period_result is None (defensive error case)
        self.pu._multi_period_result = None

        # Execute & Verify: RuntimeError is raised
        mock_context = mock.MagicMock()
        with pytest.raises(RuntimeError, match='Expected cached multi-period result to be available'):
            self.pu.optimize(2021, mock_context)
