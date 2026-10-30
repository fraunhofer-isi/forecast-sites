# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder positive paths (values above MIN_VALUE)."""

import unittest
from unittest import mock

from route_analysis.upstream_chain_builder import UpstreamChain, UpstreamChainBuilder


class TestUpstreamChainBuilderPositivePaths(unittest.TestCase):
    """Tests for positive paths (values above MIN_VALUE) that execute append logic."""

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

    def test_append_energy_demands_feedstock_above_min_value(self):
        """Test _append_energy_demands appends feedstock when above MIN_VALUE (lines 134-135)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        self.builder._energy_demand_by_process = {}
        self.builder._carrier_feedstock_by_process = {1: [(5, 100.0)]}
        self.builder._append_carrier_sources = mock.MagicMock()

        self.builder._append_energy_demands(chain, enqueue_mock, 1, 1.0, 0)

        assert len(chain.energy_demands) == 1
        assert chain.energy_demands[0] == (1, 5, 100.0, 'feedstock')
        self.builder._append_carrier_sources.assert_called_once()

    def test_append_carrier_sources_significant_internal_share(self):
        """Test _append_carrier_sources appends when internal share is significant (lines 151-157)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        self.builder._split_carrier_pool = mock.MagicMock(return_value=(80.0, 20.0))
        # Two producers: one significant, one tiny (to hit line 154 continue)
        self.builder._carrier_producers = mock.MagicMock(return_value=[(10, 80.0), (11, 1e-15)])

        self.builder._append_carrier_sources(chain, enqueue_mock, 2, 5, 100.0, 0)

        # First producer has significant share, second is skipped (line 154)
        assert len(chain.internal_carrier_pool_inputs) == 1
        assert len(chain.carrier_flows) == 1
        enqueue_mock.assert_called_once()

    def test_append_carrier_sources_no_purchased_amount(self):
        """Test _append_carrier_sources with zero purchased amount (branch 156->exit)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        # All internal, no purchased (purchased_required_gj = 0)
        self.builder._split_carrier_pool = mock.MagicMock(return_value=(100.0, 0.0))
        self.builder._carrier_producers = mock.MagicMock(return_value=[(10, 100.0)])

        self.builder._append_carrier_sources(chain, enqueue_mock, 2, 5, 100.0, 0)

        # Internal flows appended, but NO purchased_carrier_flows (branch 156->exit)
        assert len(chain.internal_carrier_pool_inputs) == 1
        assert len(chain.purchased_carrier_flows) == 0

    def test_append_product_feedstock_flows_significant_producer_share(self):
        """Test _append_product_feedstock_flows with significant producer share (line 178)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        self.builder._product_feedstock_by_process = {1: [(10, 100.0)]}
        # Two producers: one significant, one tiny (to hit line 178 continue)
        self.builder._product_producers = mock.MagicMock(return_value=[(20, 100.0), (21, 1e-15)])

        self.builder._append_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # First producer appended, second skipped (line 178)
        assert len(chain.product_flows) == 1
        enqueue_mock.assert_called_once()

    def test_append_by_product_feedstock_flows_significant_producer_share(self):
        """Test _append_by_product_feedstock_flows with significant producer share (line 200)."""
        chain = UpstreamChain()
        enqueue_mock = mock.MagicMock()

        self.builder._by_product_feedstock_by_process = {1: [(20, 100.0)]}
        # Two producers: one significant, one tiny (to hit line 200 continue)
        self.builder._by_product_producers = mock.MagicMock(return_value=[(30, 100.0), (31, 1e-15)])

        self.builder._append_by_product_feedstock_flows(chain, enqueue_mock, 1, 1.0, 0)

        # First producer appended, second skipped (line 200)
        assert len(chain.by_product_flows) == 1
        enqueue_mock.assert_called_once()

    def test_compute_allocation_factor_no_same_kind_outputs(self):
        """Test _compute_allocation_factor falls back to all outputs (line 237)."""
        self.builder._product_outputs_by_process = {}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {1: [(5, 100.0)]}

        result = self.builder._compute_allocation_factor(1, 'product', 10, 50.0, 't')

        assert result == 0.5

    def test_compute_allocation_factor_zero_total_basis(self):
        """Test _compute_allocation_factor returns 0 when total_basis <= MIN_VALUE (line 241)."""
        self.builder._product_outputs_by_process = {1: [(10, 0.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}

        result = self.builder._compute_allocation_factor(1, 'product', 10, 50.0, 't')

        assert result == 0.0

    def test_trace_upstream_processes_chain(self):
        """Test trace_upstream processes full chain (lines 104, 109 via integration)."""
        self.builder._product_producers_by_id = {10: [(1, 100.0)]}
        self.builder._product_outputs_by_process = {1: [(10, 100.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}
        self.builder._energy_demand_by_process = {}
        self.builder._carrier_feedstock_by_process = {}
        self.builder._product_feedstock_by_process = {}
        self.builder._by_product_feedstock_by_process = {}
        self.builder._carrier_producers_by_id = {}
        self.builder._purchased_carriers = {}

        chain = self.builder.trace_upstream(10)

        assert len(chain.final_product_outputs) == 1
        assert 1 in chain.process_ids

    def test_trace_upstream_depth_exceeds_max(self):
        """Test trace_upstream with circular chain exercises re-queuing (branch 89->exit)."""
        # Process 1 and 2 both produce product 10
        # Process 1 needs product 10 as feedstock (creates circular dependency)
        # When processing process 1's feedstock, enqueue is called for both producers
        # Process 2 gets enqueued twice: once from initial producers, once from feedstock
        self.builder._product_producers_by_id = {10: [(1, 100.0), (2, 50.0)]}
        self.builder._product_outputs_by_process = {1: [(10, 100.0)], 2: [(10, 50.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}
        self.builder._energy_demand_by_process = {}
        self.builder._carrier_feedstock_by_process = {}
        # Process 1 needs product 10 → enqueue called for producers 1 and 2
        # But producer 2 is already in queue from initial step → branch 89->exit
        self.builder._product_feedstock_by_process = {1: [(10, 80.0)]}
        self.builder._by_product_feedstock_by_process = {}
        self.builder._carrier_producers_by_id = {}
        self.builder._purchased_carriers = {}

        chain = self.builder.trace_upstream(10)

        assert 1 in chain.process_ids
        assert 2 in chain.process_ids

    def test_trace_upstream_enqueue_with_zero_amount(self):
        """Test trace_upstream enqueue early-returns for zero amount (branch 89->exit)."""
        # Process 1 produces product 10, and has energy demand for carrier 5
        # but the carrier has zero production (purchased only)
        self.builder._product_producers_by_id = {10: [(1, 100.0)]}
        self.builder._product_outputs_by_process = {1: [(10, 100.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}
        # Energy demand that will trigger _append_carrier_sources
        self.builder._energy_demand_by_process = {1: [(5, 50.0)]}
        self.builder._carrier_feedstock_by_process = {}
        self.builder._product_feedstock_by_process = {}
        self.builder._by_product_feedstock_by_process = {}
        # Carrier 5 has zero internal production → enqueue called with 0 amount
        self.builder._carrier_producers_by_id = {}
        self.builder._purchased_carriers = {5: 50.0}

        chain = self.builder.trace_upstream(10)

        assert 1 in chain.process_ids
        assert len(chain.energy_demands) == 1

    def test_trace_upstream_no_product_feedstock(self):
        """Test trace_upstream with no product feedstock (branch 161->exit)."""
        self.builder._product_producers_by_id = {10: [(1, 100.0)]}
        self.builder._product_outputs_by_process = {1: [(10, 100.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}
        self.builder._energy_demand_by_process = {}
        self.builder._carrier_feedstock_by_process = {}
        # No product feedstock for process 1 → _append_product_feedstock_flows returns immediately
        self.builder._product_feedstock_by_process = {}
        self.builder._by_product_feedstock_by_process = {}
        self.builder._carrier_producers_by_id = {}
        self.builder._purchased_carriers = {}

        chain = self.builder.trace_upstream(10)

        assert 1 in chain.process_ids

    def test_trace_upstream_allocation_factor_zero(self):
        """Test trace_upstream skips when allocation_factor is zero (line 241 via 112-113)."""
        # Process 1 produces product 10 but with zero output amount
        self.builder._product_producers_by_id = {10: [(1, 100.0)]}
        # Process outputs are all zero → _compute_allocation_factor returns 0
        self.builder._product_outputs_by_process = {1: [(10, 1e-15)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}
        self.builder._energy_demand_by_process = {}
        self.builder._carrier_feedstock_by_process = {}
        self.builder._product_feedstock_by_process = {}
        self.builder._by_product_feedstock_by_process = {}
        self.builder._carrier_producers_by_id = {}
        self.builder._purchased_carriers = {}

        chain = self.builder.trace_upstream(10)

        # Process is enqueued but allocation factor is 0 → skipped
        assert len(chain.final_product_outputs) == 1
        assert len(chain.process_ids) == 0
