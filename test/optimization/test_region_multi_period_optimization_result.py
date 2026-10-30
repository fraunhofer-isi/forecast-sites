# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for RegionMultiPeriodOptimizationResult class."""

import unittest
from unittest import mock

from optimization.optimization_result import OptimizationResult
from optimization.region_multi_period_optimization_result import RegionMultiPeriodOptimizationResult


class TestRegionMultiPeriodOptimizationResult(unittest.TestCase):
    """Tests for RegionMultiPeriodOptimizationResult."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_pu_1 = mock.MagicMock()
        self.mock_pu_1.__hash__ = lambda s: 1
        self.mock_pu_1.__eq__ = lambda s, o: s is o

        self.mock_pu_2 = mock.MagicMock()
        self.mock_pu_2.__hash__ = lambda s: 2
        self.mock_pu_2.__eq__ = lambda s, o: s is o

        self.mock_carrier_1 = mock.MagicMock()
        self.mock_carrier_2 = mock.MagicMock()

        self.mock_process_option_1 = mock.MagicMock()
        self.mock_process_option_2 = mock.MagicMock()

        self.production_units = [self.mock_pu_1, self.mock_pu_2]
        self.carriers = [self.mock_carrier_1, self.mock_carrier_2]
        self.process_options = [self.mock_process_option_1, self.mock_process_option_2]
        self.simulation_periods = [2020, 2025, 2030]

        self.process_options_by_pu = {
            self.mock_pu_1: self.process_options,
            self.mock_pu_2: self.process_options,
        }

        self.num_proc_by_pu = {
            self.mock_pu_1: 2,
            self.mock_pu_2: 2,
        }

        self.vars_per_period_by_pu = {
            self.mock_pu_1: 4,  # 2 processes + 2 carriers
            self.mock_pu_2: 4,
        }

        self.offsets_by_pu = {
            self.mock_pu_1: 0,
            self.mock_pu_2: 12,  # 4 vars * 3 periods
        }

        self.new_capacity_offsets_by_pu = {
            self.mock_pu_1: 24,  # After exec+carrier section
            self.mock_pu_2: 30,  # 24 + 6 new_capacity vars for pu_1
        }

        # Create mock LP solution
        # For simplicity: all variables set to specific values
        solution_size = 36  # 2 PUs * 4 vars * 3 periods + 2 PUs * 2 proc * 3 periods
        self.solution_values = list(range(1, solution_size + 1))
        self.mock_lp_result = mock.MagicMock()
        self.mock_lp_result.x = self.solution_values

    def test_init_stores_production_units_as_list(self):
        """Test that production units are stored as a list."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        assert isinstance(result._production_units, list)
        assert len(result._production_units) == 2

    def test_init_stores_carriers_as_list(self):
        """Test that carriers are stored as a list."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        assert isinstance(result._carriers, list)
        assert len(result._carriers) == 2

    def test_init_stores_simulation_periods_as_list(self):
        """Test that simulation periods are stored as a list."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        assert isinstance(result._simulation_periods, list)
        assert result._simulation_periods == [2020, 2025, 2030]

    def test_init_stores_total_cost(self):
        """Test that total cost is stored."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
            total_cost_in_euro=1000.5,
        )
        assert result.total_cost_in_euro == 1000.5

    def test_init_total_cost_none(self):
        """Test that total_cost_in_euro can be None."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
            total_cost_in_euro=None,
        )
        assert result.total_cost_in_euro is None

    def test_init_total_cost_default_none(self):
        """Test that total_cost_in_euro defaults to None."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        assert result.total_cost_in_euro is None

    def test_init_total_cost_converted_to_float(self):
        """Test that total_cost is converted to float."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
            total_cost_in_euro=500,  # int
        )
        assert isinstance(result.total_cost_in_euro, float)
        assert result.total_cost_in_euro == 500.0

    def test_has_result_for_year_true(self):
        """Test has_result_for_year returns True for existing years."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        assert result.has_result_for_year(2020)
        assert result.has_result_for_year(2025)
        assert result.has_result_for_year(2030)

    def test_has_result_for_year_false(self):
        """Test has_result_for_year returns False for non-existent years."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        assert not result.has_result_for_year(2019)
        assert not result.has_result_for_year(2024)
        assert not result.has_result_for_year(2031)

    def test_result_for_year_returns_dict(self):
        """Test that result_for_year returns a dict of PU results."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        year_result = result.result_for_year(2020)
        assert isinstance(year_result, dict)
        assert len(year_result) == 2  # 2 PUs

    def test_result_for_year_contains_optimization_results(self):
        """Test that result_for_year contains OptimizationResult objects."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        year_result = result.result_for_year(2025)
        for opt_result in year_result.values():
            assert isinstance(opt_result, OptimizationResult)

    def test_result_for_with_year(self):
        """Test result_for with explicit year."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        pu_result = result.result_for(self.mock_pu_1, year=2025)
        assert isinstance(pu_result, OptimizationResult)

    def test_result_for_without_year_uses_first_period(self):
        """Test result_for without year uses first simulation period."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        pu_result = result.result_for(self.mock_pu_1)
        expected_result = result.result_for(self.mock_pu_1, year=2020)
        # Compare the underlying dicts since OptimizationResult doesn't override __eq__
        assert pu_result.process_execution_counts == expected_result.process_execution_counts

    def test_new_capacity_for_year_returns_dict(self):
        """Test that new_capacity_for_year returns a dict."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        new_cap = result.new_capacity_for_year(2020)
        assert isinstance(new_cap, dict)
        assert len(new_cap) == 2  # 2 PUs

    def test_new_capacity_for_year_values_are_floats(self):
        """Test that new capacity values are floats."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        new_cap = result.new_capacity_for_year(2025)
        for capacity_dict in new_cap.values():
            assert isinstance(capacity_dict, dict)
            for capacity_value in capacity_dict.values():
                assert isinstance(capacity_value, float)

    def test_simulation_periods_property(self):
        """Test simulation_periods property."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        periods = result.simulation_periods
        assert periods == [2020, 2025, 2030]

    def test_simulation_periods_property_returns_copy(self):
        """Test that simulation_periods property returns a copy."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        periods1 = result.simulation_periods
        periods2 = result.simulation_periods
        assert periods1 == periods2
        # Verify they are different list objects
        assert periods1 is not periods2

    def test_process_execution_counts_extracted(self):
        """Test that process execution counts are extracted from LP solution."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        year_result = result.result_for_year(2020)
        pu_result = year_result[self.mock_pu_1]
        # Check that process execution counts were extracted
        assert pu_result.process_execution_counts is not None
        assert len(pu_result.process_execution_counts) == 2

    def test_purchased_carrier_amounts_extracted(self):
        """Test that purchased carrier amounts are extracted from LP solution."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        year_result = result.result_for_year(2020)
        pu_result = year_result[self.mock_pu_1]
        # Check that purchased carrier amounts were extracted
        assert pu_result.purchased_carrier_amounts is not None
        assert len(pu_result.purchased_carrier_amounts) == 2

    def test_all_years_have_results(self):
        """Test that all simulation periods have results."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        for year in self.simulation_periods:
            assert result.has_result_for_year(year)
            year_result = result.result_for_year(year)
            assert len(year_result) == 2  # 2 PUs

    def test_all_years_have_new_capacity(self):
        """Test that all simulation periods have new capacity data."""
        result = RegionMultiPeriodOptimizationResult(
            self.mock_lp_result,
            self.production_units,
            self.process_options_by_pu,
            self.carriers,
            self.simulation_periods,
            self.offsets_by_pu,
            self.new_capacity_offsets_by_pu,
            self.num_proc_by_pu,
            self.vars_per_period_by_pu,
        )
        for year in self.simulation_periods:
            new_cap = result.new_capacity_for_year(year)
            assert len(new_cap) == 2  # 2 PUs


if __name__ == '__main__':
    unittest.main()
