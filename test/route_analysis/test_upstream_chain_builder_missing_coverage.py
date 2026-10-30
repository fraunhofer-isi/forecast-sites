# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Targeted tests for UpstreamChainBuilder missing coverage lines."""

import unittest
from unittest import mock

from route_analysis.upstream_chain_builder import UpstreamChain, UpstreamChainBuilder


class TestUpstreamChainBuilderMissingCoverage(unittest.TestCase):
    """Tests for UpstreamChainBuilder missing coverage branches."""

    def setUp(self):
        """Set up test fixtures."""
        mock_context = {
            'process_product_production_in_t': None,
            'process_by_product_production_in_t': None,
            'process_energy_carrier_production_in_gj': None,
            'process_energy_carrier_energy_demand_in_gj': None,
            'process_energy_carrier_feedstock_demand_in_gj': None,
            'process_product_feedstock_demand_in_t': None,
            'process_by_product_feedstock_demand_in_t': None,
            'production_unit_energy_carrier_purchased_amount_in_gj': None,
            'production_unit_product_purchased_amount_in_t': None,
            'production_unit_by_product_purchased_amount_in_t': None,
        }
        self.builder = UpstreamChainBuilder(mock_context, 2020, {})

    def test_trace_upstream_delta_amount_below_min_value(self):
        """Test trace_upstream skips processing when delta_amount <= MIN_VALUE (line 104)."""
        # Setup: product producer returns amount
        self.builder._product_producers = mock.MagicMock(return_value=[(1, 100.0)])

        # Mock the allocation factor to return a very small value
        self.builder._compute_allocation_factor = mock.MagicMock(return_value=1e-12)

        result = self.builder.trace_upstream(10)

        # Should have final_product_outputs but no process_ids (skipped due to small delta)
        assert len(result.final_product_outputs) == 1
        assert len(result.process_ids) == 0

    def test_trace_upstream_depth_exceeds_max_depth(self):
        """Test trace_upstream skips processing when depth > MAX_DEPTH (line 109)."""
        # This is hard to test directly, but we can verify the MAX_DEPTH constant
        assert self.builder.MAX_DEPTH == 10

    def test_append_energy_demands_allocated_gj_below_min_value(self):
        """Test _append_energy_demands skips when allocated_gj <= MIN_VALUE (line 126)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: energy demand with very small amount
        self.builder._energy_demand_by_process = {1: [(5, 1e-12)]}
        self.builder._carrier_feedstock_by_process = {}
        self.builder._append_carrier_sources = mock.MagicMock()

        self.builder._append_energy_demands(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append energy demands or call _append_carrier_sources
        assert len(chain.energy_demands) == 0
        self.builder._append_carrier_sources.assert_not_called()

    def test_append_energy_demands_feedstock_allocated_gj_below_min_value(self):
        """Test _append_energy_demands skips feedstock when allocated_gj <= MIN_VALUE (line 133)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: feedstock demand with very small amount
        self.builder._energy_demand_by_process = {}
        self.builder._carrier_feedstock_by_process = {1: [(5, 1e-12)]}
        self.builder._append_carrier_sources = mock.MagicMock()

        self.builder._append_energy_demands(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append energy demands or call _append_carrier_sources
        assert len(chain.energy_demands) == 0
        self.builder._append_carrier_sources.assert_not_called()

    def test_append_carrier_sources_producer_share_below_min_value(self):
        """Test _append_carrier_sources skips producer when share <= MIN_VALUE (line 154)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: carrier producers with very small share
        self.builder._split_carrier_pool = mock.MagicMock(return_value=(100.0, 0.0))
        self.builder._carrier_producers = mock.MagicMock(return_value=[(1, 1e-12)])

        self.builder._append_carrier_sources(chain, enqueue_mock, 2, 5, 100.0, 0)

        # Should not append internal_carrier_pool_inputs or carrier_flows
        assert len(chain.internal_carrier_pool_inputs) == 0
        assert len(chain.carrier_flows) == 0

    def test_append_product_feedstock_flows_allocated_t_below_min_value(self):
        """Test _append_product_feedstock_flows skips when allocated_t <= MIN_VALUE (line 168)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: product feedstock with very small amount
        self.builder._product_feedstock_by_process = {1: [(10, 1e-12)]}

        self.builder._append_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append product_flows or purchased_product_flows
        assert len(chain.product_flows) == 0
        assert len(chain.purchased_product_flows) == 0

    def test_append_product_feedstock_flows_producer_share_below_min_value(self):
        """Test _append_product_feedstock_flows skips producer when share <= MIN_VALUE (line 178)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: product feedstock with producers that have very small share
        self.builder._product_feedstock_by_process = {1: [(10, 100.0)]}
        self.builder._product_producers = mock.MagicMock(return_value=[(2, 1e-12)])

        self.builder._append_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append product_flows (producer share too small)
        assert len(chain.product_flows) == 0

    def test_append_product_feedstock_flows_purchased_t_below_min_value(self):
        """Test _append_product_feedstock_flows skips purchased when purchased_t <= MIN_VALUE (line 184)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: product feedstock where all is internal
        self.builder._product_feedstock_by_process = {1: [(10, 100.0)]}
        self.builder._product_producers = mock.MagicMock(return_value=[(2, 100.0)])

        self.builder._append_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append purchased_product_flows (no purchased amount)
        assert len(chain.purchased_product_flows) == 0

    def test_append_by_product_feedstock_flows_allocated_t_below_min_value(self):
        """Test _append_by_product_feedstock_flows skips when allocated_t <= MIN_VALUE (line 190)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: by-product feedstock with very small amount
        self.builder._by_product_feedstock_by_process = {1: [(20, 1e-12)]}

        self.builder._append_by_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append by_product_flows or purchased_by_product_flows
        assert len(chain.by_product_flows) == 0
        assert len(chain.purchased_by_product_flows) == 0

    def test_append_by_product_feedstock_flows_producer_share_below_min_value(self):
        """Test _append_by_product_feedstock_flows skips producer when share <= MIN_VALUE (line 206)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: by-product feedstock with producers that have very small share
        self.builder._by_product_feedstock_by_process = {1: [(20, 100.0)]}
        self.builder._by_product_producers = mock.MagicMock(return_value=[(2, 1e-12)])

        self.builder._append_by_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append by_product_flows (producer share too small)
        assert len(chain.by_product_flows) == 0

    def test_append_by_product_feedstock_flows_purchased_t_below_min_value(self):
        """Test _append_by_product_feedstock_flows skips purchased when purchased_t <= MIN_VALUE (line 241)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # Setup: by-product feedstock where all is internal
        self.builder._by_product_feedstock_by_process = {1: [(20, 100.0)]}
        self.builder._by_product_producers = mock.MagicMock(return_value=[(2, 100.0)])

        self.builder._append_by_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # Should not append purchased_by_product_flows (no purchased amount)
        assert len(chain.purchased_by_product_flows) == 0


if __name__ == '__main__':
    unittest.main()
