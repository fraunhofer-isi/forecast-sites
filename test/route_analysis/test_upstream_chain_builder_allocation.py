# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder helper methods."""

import unittest

import pytest

from route_analysis.upstream_chain_builder import UpstreamChainBuilder


class TestUpstreamChainBuilderComputeAllocationFactor(unittest.TestCase):
    """Test UpstreamChainBuilder._compute_allocation_factor method."""

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

    def test_compute_allocation_factor_no_outputs(self):
        """Test _compute_allocation_factor returns 0 when no outputs."""
        self.builder._product_outputs_by_process = {}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}

        factor = self.builder._compute_allocation_factor(1, 'product', 1, 100.0, 't')

        assert factor == 0.0

    def test_compute_allocation_factor_with_matching_output(self):
        """Test _compute_allocation_factor with matching output kind."""
        # Setup: process 1 produces 100t of product 1
        self.builder._product_outputs_by_process = {1: [(1, 100.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}

        # Request 50t of product 1
        factor = self.builder._compute_allocation_factor(1, 'product', 1, 50.0, 't')

        # Factor should be 50/100 = 0.5
        assert factor == pytest.approx(0.5)

    def test_compute_allocation_factor_clamped_to_one(self):
        """Test _compute_allocation_factor is clamped to 1.0."""
        # Setup: process 1 produces 50t of product 1
        self.builder._product_outputs_by_process = {1: [(1, 50.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}

        # Request 100t of product 1 (more than available)
        factor = self.builder._compute_allocation_factor(1, 'product', 1, 100.0, 't')

        # Factor should be clamped to 1.0
        assert factor == 1.0

    def test_compute_allocation_factor_zero_basis(self):
        """Test _compute_allocation_factor returns 0 when total basis is zero."""
        # Setup: process 1 produces 0t of product 1
        self.builder._product_outputs_by_process = {1: [(1, 0.0)]}
        self.builder._by_product_outputs_by_process = {}
        self.builder._carrier_outputs_by_process = {}

        factor = self.builder._compute_allocation_factor(1, 'product', 1, 50.0, 't')

        assert factor == 0.0
