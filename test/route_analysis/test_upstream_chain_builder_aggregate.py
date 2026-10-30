# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for UpstreamChainBuilder aggregate methods."""

import unittest

import pandas as pd

from route_analysis.upstream_chain_builder import UpstreamChainBuilder


class TestUpstreamChainBuilderAggregateProcessTable(unittest.TestCase):
    """Test UpstreamChainBuilder._aggregate_process_table method."""

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

    def test_aggregate_process_table_with_none(self):
        """Test _aggregate_process_table returns empty dict for None."""
        result = self.builder._aggregate_process_table(None, 'id_product')
        assert result == {}

    def test_aggregate_process_table_with_empty_dataframe(self):
        """Test _aggregate_process_table returns empty dict for empty DataFrame."""
        df = pd.DataFrame()
        result = self.builder._aggregate_process_table(df, 'id_product')
        assert result == {}

    def test_aggregate_process_table_missing_year_column(self):
        """Test _aggregate_process_table returns empty dict when year column missing."""
        df = pd.DataFrame(
            {
                'id_process': [1, 2],
                'id_product': [10, 20],
            }
        )
        result = self.builder._aggregate_process_table(df, 'id_product')
        assert result == {}

    def test_aggregate_process_table_with_data(self):
        """Test _aggregate_process_table aggregates data correctly."""
        df = pd.DataFrame(
            {
                'id_process': [1, 1, 2],
                'id_product': [10, 10, 20],
                'Y2020': [100.0, 50.0, 200.0],
            }
        )
        result = self.builder._aggregate_process_table(df, 'id_product')

        # Process 1, product 10: 100 + 50 = 150
        assert (1, 10) in result
        assert result[1, 10] == 150.0

        # Process 2, product 20: 200
        assert (2, 20) in result
        assert result[2, 20] == 200.0

    def test_aggregate_process_table_filters_small_values(self):
        """Test _aggregate_process_table filters values below MIN_VALUE."""
        df = pd.DataFrame(
            {
                'id_process': [1, 2],
                'id_product': [10, 20],
                'Y2020': [1e-10, 100.0],  # First value below MIN_VALUE
            }
        )
        result = self.builder._aggregate_process_table(df, 'id_product')

        # Small value should be filtered out
        assert (1, 10) not in result
        # Large value should be included
        assert (2, 20) in result
