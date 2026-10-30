# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder._split_carrier_pool method."""

import unittest

import pytest

from route_analysis.upstream_chain_builder import UpstreamChainBuilder


class TestUpstreamChainBuilderSplitCarrierPool(unittest.TestCase):
    """Test UpstreamChainBuilder._split_carrier_pool method."""

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

    def test_split_carrier_pool_empty_pool(self):
        """Test _split_carrier_pool with empty pool."""
        self.builder._carrier_producers_by_id = {}
        self.builder._purchased_carriers = {}

        internal, purchased = self.builder._split_carrier_pool(1, 100.0)

        # All should be purchased when pool is empty
        assert internal == 0.0
        assert purchased == 100.0

    def test_split_carrier_pool_only_internal(self):
        """Test _split_carrier_pool with only internal production."""
        # Carrier 1 produced by process 1 (100 GJ)
        self.builder._carrier_producers_by_id = {1: [(1, 100.0)]}
        self.builder._purchased_carriers = {}

        internal, purchased = self.builder._split_carrier_pool(1, 100.0)

        # All should be internal
        assert internal == 100.0
        assert purchased == 0.0

    def test_split_carrier_pool_only_purchased(self):
        """Test _split_carrier_pool with only purchased."""
        self.builder._carrier_producers_by_id = {}
        self.builder._purchased_carriers = {1: 100.0}

        internal, purchased = self.builder._split_carrier_pool(1, 100.0)

        # All should be purchased
        assert internal == 0.0
        assert purchased == 100.0

    def test_split_carrier_pool_mixed(self):
        """Test _split_carrier_pool with mixed internal and purchased."""
        # Carrier 1: 100 GJ internal, 100 GJ purchased (50/50 split)
        self.builder._carrier_producers_by_id = {1: [(1, 100.0)]}
        self.builder._purchased_carriers = {1: 100.0}

        internal, purchased = self.builder._split_carrier_pool(1, 100.0)

        # Should split 50/50
        assert internal == pytest.approx(50.0)
        assert purchased == pytest.approx(50.0)
