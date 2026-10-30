# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for RegionResultApplier class."""

import unittest
from unittest import mock

from region.region_new_capacity_adapter import _RegionNewCapacityAdapter
from region.region_result_applier import RegionResultApplier


class TestRegionNewCapacityAdapter(unittest.TestCase):
    """Tests for _RegionNewCapacityAdapter."""

    def test_init_stores_capacity_counts(self):
        """Test that new_capacity_counts are stored."""
        capacity_counts = {'process_1': 5, 'process_2': 10}
        adapter = _RegionNewCapacityAdapter(capacity_counts)
        assert adapter._new_capacity_counts == capacity_counts

    def test_get_new_capacity_for_year_returns_counts(self):
        """Test that get_new_capacity_for_year returns stored counts."""
        capacity_counts = {'process_1': 5, 'process_2': 10}
        adapter = _RegionNewCapacityAdapter(capacity_counts)
        result = adapter.get_new_capacity_for_year(2020)
        assert result == capacity_counts

    def test_get_new_capacity_for_year_ignores_year(self):
        """Test that year parameter is ignored."""
        capacity_counts = {'process_1': 5}
        adapter = _RegionNewCapacityAdapter(capacity_counts)
        # Same result for any year
        result_2020 = adapter.get_new_capacity_for_year(2020)
        result_2021 = adapter.get_new_capacity_for_year(2021)
        assert result_2020 == result_2021
        assert result_2020 == capacity_counts

    def test_get_new_capacity_for_year_empty_dict(self):
        """Test with empty capacity dict."""
        adapter = _RegionNewCapacityAdapter({})
        result = adapter.get_new_capacity_for_year(2020)
        assert result == {}


class TestRegionResultApplierAssignResults(unittest.TestCase):
    """Tests for result assignment methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.applier = RegionResultApplier()

    def test_assign_results_single_production_unit(self):
        """Test assigning results to single production unit."""
        mock_pu = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_region_result = mock.MagicMock()
        mock_region_result.result_for = mock.MagicMock(return_value=mock_result)

        self.applier._assign_results(mock_region_result, [mock_pu])

        mock_region_result.result_for.assert_called_once_with(mock_pu)
        assert mock_pu.optimization_results == mock_result

    def test_assign_results_multiple_production_units(self):
        """Test assigning results to multiple production units."""
        mock_pu_1 = mock.MagicMock()
        mock_pu_2 = mock.MagicMock()
        mock_result_1 = mock.MagicMock()
        mock_result_2 = mock.MagicMock()
        mock_region_result = mock.MagicMock()
        mock_region_result.result_for = mock.MagicMock(side_effect=[mock_result_1, mock_result_2])

        self.applier._assign_results(mock_region_result, [mock_pu_1, mock_pu_2])

        assert mock_region_result.result_for.call_count == 2
        assert mock_pu_1.optimization_results == mock_result_1
        assert mock_pu_2.optimization_results == mock_result_2

    def test_assign_results_empty_production_units(self):
        """Test assigning results with no production units."""
        mock_region_result = mock.MagicMock()
        self.applier._assign_results(mock_region_result, [])
        mock_region_result.result_for.assert_not_called()

    def test_assign_results_for_year_single_production_unit(self):
        """Test assigning results for specific year."""
        mock_pu = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_multi_result = mock.MagicMock()
        mock_multi_result.result_for = mock.MagicMock(return_value=mock_result)

        self.applier._assign_results_for_year(2020, mock_multi_result, [mock_pu])

        mock_multi_result.result_for.assert_called_once_with(mock_pu, 2020)
        assert mock_pu.optimization_results == mock_result

    def test_assign_results_for_year_multiple_production_units(self):
        """Test assigning multi-period results to multiple units."""
        mock_pu_1 = mock.MagicMock()
        mock_pu_2 = mock.MagicMock()
        mock_result_1 = mock.MagicMock()
        mock_result_2 = mock.MagicMock()
        mock_multi_result = mock.MagicMock()
        mock_multi_result.result_for = mock.MagicMock(side_effect=[mock_result_1, mock_result_2])

        self.applier._assign_results_for_year(2020, mock_multi_result, [mock_pu_1, mock_pu_2])

        assert mock_multi_result.result_for.call_count == 2
        assert mock_pu_1.optimization_results == mock_result_1
        assert mock_pu_2.optimization_results == mock_result_2


class TestRegionResultApplierUpdateSubUnits(unittest.TestCase):
    """Tests for sub-production-unit updates."""

    def setUp(self):
        """Set up test fixtures."""
        self.applier = RegionResultApplier()

    def test_update_sub_production_units_single_unit(self):
        """Test updating sub-units for single production unit."""
        mock_pu = mock.MagicMock()
        self.applier._update_sub_production_units(2020, [mock_pu])
        mock_pu._create_or_update_sub_production_units.assert_called_once_with(2020)

    def test_update_sub_production_units_multiple_units(self):
        """Test updating sub-units for multiple production units."""
        mock_pu_1 = mock.MagicMock()
        mock_pu_2 = mock.MagicMock()
        self.applier._update_sub_production_units(2020, [mock_pu_1, mock_pu_2])
        mock_pu_1._create_or_update_sub_production_units.assert_called_once_with(2020)
        mock_pu_2._create_or_update_sub_production_units.assert_called_once_with(2020)

    def test_update_sub_production_units_different_years(self):
        """Test with different years."""
        mock_pu = mock.MagicMock()
        self.applier._update_sub_production_units(2025, [mock_pu])
        mock_pu._create_or_update_sub_production_units.assert_called_once_with(2025)

    def test_update_sub_production_units_from_multi_period_single_unit(self):
        """Test updating from multi-period result."""
        mock_pu = mock.MagicMock()
        new_capacity = {'process_1': 5}
        mock_multi_result = mock.MagicMock()
        mock_multi_result.new_capacity_for_year = mock.MagicMock(return_value={mock_pu: new_capacity})

        self.applier._update_sub_production_units_from_multi_period(2020, mock_multi_result, [mock_pu])

        mock_multi_result.new_capacity_for_year.assert_called_once_with(2020)
        mock_pu._create_or_update_sub_production_units_from_multi_period.assert_called_once_with(2020)
        # Check that adapter was used and cleared
        assert mock_pu._multi_period_result is None

    def test_update_sub_production_units_from_multi_period_no_capacity_for_pu(self):
        """Test when multi-period result has no capacity for a PU."""
        mock_pu = mock.MagicMock()
        mock_multi_result = mock.MagicMock()
        mock_multi_result.new_capacity_for_year = mock.MagicMock(return_value={})

        self.applier._update_sub_production_units_from_multi_period(2020, mock_multi_result, [mock_pu])

        # Should still call update with empty dict wrapped in adapter
        mock_pu._create_or_update_sub_production_units_from_multi_period.assert_called_once_with(2020)


class TestRegionResultApplierAggregatePoolDeltas(unittest.TestCase):
    """Tests for pool delta aggregation."""

    def setUp(self):
        """Set up test fixtures."""
        self.applier = RegionResultApplier()

    def test_aggregate_pool_deltas_empty_production_units(self):
        """Test with no production units."""
        deltas = self.applier._aggregate_pool_deltas(2020, [])
        assert deltas == {}

    def test_aggregate_pool_deltas_purchased_carrier(self):
        """Test aggregating purchased carrier amounts."""
        mock_carrier = mock.MagicMock()
        mock_pool = mock.MagicMock()
        mock_site = mock.MagicMock()
        mock_site.shared_pool_for = mock.MagicMock(return_value=mock_pool)
        mock_pu = mock.MagicMock()
        mock_pu._site = mock_site
        mock_pu.purchased_carrier_amounts = {mock_carrier: 100.0}

        deltas = self.applier._aggregate_pool_deltas(2020, [mock_pu])

        key = (mock_pool, mock_carrier)
        assert key in deltas
        assert deltas[key] == 100.0

    def test_aggregate_pool_deltas_zero_purchased_carrier_skipped(self):
        """Test that zero purchased amounts are skipped."""
        mock_carrier = mock.MagicMock()
        mock_site = mock.MagicMock()
        mock_pu = mock.MagicMock()
        mock_pu._site = mock_site
        mock_pu.purchased_carrier_amounts = {mock_carrier: 0}
        mock_pu.available_carriers = []

        deltas = self.applier._aggregate_pool_deltas(2020, [mock_pu])

        assert deltas == {}
        mock_site.shared_pool_for.assert_not_called()

    def test_aggregate_pool_deltas_multiple_purchased_carriers(self):
        """Test with multiple purchased carriers from same PU."""
        mock_carrier_1 = mock.MagicMock()
        mock_carrier_2 = mock.MagicMock()
        mock_pool = mock.MagicMock()
        mock_site = mock.MagicMock()
        mock_site.shared_pool_for = mock.MagicMock(return_value=mock_pool)
        mock_pu = mock.MagicMock()
        mock_pu._site = mock_site
        mock_pu.purchased_carrier_amounts = {mock_carrier_1: 100.0, mock_carrier_2: 50.0}

        deltas = self.applier._aggregate_pool_deltas(2020, [mock_pu])

        key_1 = (mock_pool, mock_carrier_1)
        key_2 = (mock_pool, mock_carrier_2)
        assert deltas[key_1] == 100.0
        assert deltas[key_2] == 50.0


class TestRegionResultApplierApplyPoolDeltas(unittest.TestCase):
    """Tests for applying pool deltas."""

    def setUp(self):
        """Set up test fixtures."""
        self.applier = RegionResultApplier()

    def test_apply_pool_deltas_positive_amount(self):
        """Test applying delta when there is a purchased amount."""
        mock_pool = mock.MagicMock()
        mock_carrier = mock.MagicMock()
        mock_context = mock.MagicMock()
        pool_deltas = {(mock_pool, mock_carrier): 100.0}

        self.applier._apply_pool_deltas(2020, pool_deltas, mock_context)

        mock_pool.consume_purchased_carrier_amount.assert_called_once_with(mock_carrier, 100.0, 2020, mock_context)

    def test_apply_pool_deltas_zero_amount_skipped(self):
        """Test that a zero amount does not call consume."""
        mock_pool = mock.MagicMock()
        mock_carrier = mock.MagicMock()
        mock_context = mock.MagicMock()
        pool_deltas = {(mock_pool, mock_carrier): 0.0}

        self.applier._apply_pool_deltas(2020, pool_deltas, mock_context)

        mock_pool.consume_purchased_carrier_amount.assert_not_called()

    def test_apply_pool_deltas_empty(self):
        """Test applying empty deltas."""
        mock_context = mock.MagicMock()
        self.applier._apply_pool_deltas(2020, {}, mock_context)
        # Should complete without errors

    def test_apply_pool_deltas_multiple_pools(self):
        """Test applying deltas for multiple pools."""
        mock_pool_1 = mock.MagicMock()
        mock_pool_2 = mock.MagicMock()
        mock_carrier = mock.MagicMock()
        mock_context = mock.MagicMock()
        pool_deltas = {
            (mock_pool_1, mock_carrier): 100.0,
            (mock_pool_2, mock_carrier): 50.0,
        }

        self.applier._apply_pool_deltas(2020, pool_deltas, mock_context)

        mock_pool_1.consume_purchased_carrier_amount.assert_called_once_with(mock_carrier, 100.0, 2020, mock_context)
        mock_pool_2.consume_purchased_carrier_amount.assert_called_once_with(mock_carrier, 50.0, 2020, mock_context)


class TestRegionResultApplierIntegration(unittest.TestCase):
    """Integration tests for apply methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.applier = RegionResultApplier()

    def test_apply_calls_all_steps(self):
        """Test that apply method calls all sub-methods."""
        mock_year = 2020
        mock_region_result = mock.MagicMock()
        mock_pu = mock.MagicMock()
        mock_pu.optimization_results = mock.MagicMock()
        mock_pu.purchased_carrier_amounts = {}
        mock_pu.available_carriers = []
        mock_pu._site = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_region_result.result_for = mock.MagicMock(return_value=mock_pu.optimization_results)

        self.applier.apply(mock_year, mock_region_result, [mock_pu], mock_context)

        mock_region_result.result_for.assert_called_once()
        mock_pu._create_or_update_sub_production_units.assert_called_once()

    def test_apply_for_year_calls_all_steps(self):
        """Test that apply_for_year calls all sub-methods."""
        mock_year = 2020
        mock_multi_result = mock.MagicMock()
        mock_pu = mock.MagicMock()
        mock_pu.optimization_results = mock.MagicMock()
        mock_pu.purchased_carrier_amounts = {}
        mock_pu.available_carriers = []
        mock_pu._site = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_multi_result.result_for = mock.MagicMock(return_value=mock_pu.optimization_results)
        mock_multi_result.new_capacity_for_year = mock.MagicMock(return_value={})

        self.applier.apply_for_year(mock_year, mock_multi_result, [mock_pu], mock_context)

        mock_multi_result.result_for.assert_called_once()
        mock_multi_result.new_capacity_for_year.assert_called_once()
        mock_pu._create_or_update_sub_production_units_from_multi_period.assert_called_once()


if __name__ == '__main__':
    unittest.main()
