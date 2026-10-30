# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder edge case branches."""

import unittest
from unittest import mock

from route_analysis.upstream_chain_builder import UpstreamChainBuilder


class TestUpstreamChainBuilderMinValueEdgeCase(unittest.TestCase):
    """Test UpstreamChainBuilder MIN_VALUE edge case handling."""

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

    def test_trace_upstream_with_very_small_amount(self):
        """Test trace_upstream adds to final_product_outputs but doesn't enqueue small amounts."""
        # Mock the product producers to return a very small amount
        self.builder._product_producers = mock.MagicMock(return_value=[(1, 1e-12)])

        result = self.builder.trace_upstream(10)

        # Should add to final_product_outputs but not process further (no process_ids)
        assert len(result.final_product_outputs) == 1
        assert len(result.process_ids) == 0  # Not enqueued due to MIN_VALUE

    def test_trace_upstream_with_zero_amount(self):
        """Test trace_upstream adds zero amounts to final_product_outputs but doesn't process."""
        self.builder._product_producers = mock.MagicMock(return_value=[(1, 0.0)])

        result = self.builder.trace_upstream(10)

        # Should add to final_product_outputs but not process further
        assert len(result.final_product_outputs) == 1
        assert len(result.process_ids) == 0  # Not enqueued due to MIN_VALUE
