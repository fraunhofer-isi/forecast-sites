# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnitFactory._minimum_export_interpolation_data_in_t method."""

import unittest
from unittest import mock

import pandas as pd

from production_unit.production_unit_factory import ProductionUnitFactory


class TestProductionUnitFactoryMinimumExportData(unittest.TestCase):
    """Test ProductionUnitFactory._minimum_export_interpolation_data_in_t method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_data_interface = mock.MagicMock()
        self.mock_sub_pu_factory = mock.MagicMock()
        self.mock_sector_map = {}
        self.mock_process_map = {}
        self.mock_carriers = []
        self.mock_product_map = {}
        self.mock_optimization_factory = mock.MagicMock()
        self.mock_simulation_options = {}

        self.factory = ProductionUnitFactory(
            self.mock_data_interface,
            self.mock_sub_pu_factory,
            self.mock_sector_map,
            self.mock_process_map,
            self.mock_carriers,
            self.mock_product_map,
            self.mock_optimization_factory,
            self.mock_simulation_options,
        )

    def test_minimum_export_interpolation_data_with_products(self):
        """Test _minimum_export_interpolation_data_in_t creates interpolation data for products."""
        # Create mock product
        mock_product = mock.MagicMock()
        self.factory._product_map = {501: mock_product}

        # Create DataFrame with product mapping
        df = pd.DataFrame(
            {
                'id_production_unit': [1],
                'id_product': [501],
                'minimum_export_start_year_in_t': [100.0],
                'minimum_export_interim_year_in_t': [150.0],
                'minimum_export_end_year_in_t': [200.0],
            }
        )

        self.factory._data_interface.production_unit_product_mapping = df

        result = self.factory._minimum_export_interpolation_data_in_t(1)

        # Verify result contains the product
        assert mock_product in result
        # Verify interpolation data was created
        assert result[mock_product] is not None

    def test_minimum_export_interpolation_data_empty_mapping(self):
        """Test _minimum_export_interpolation_data_in_t with empty product mapping."""
        # Create empty DataFrame
        df = pd.DataFrame(
            {
                'id_production_unit': [],
                'id_product': [],
                'minimum_export_start_year_in_t': [],
                'minimum_export_interim_year_in_t': [],
                'minimum_export_end_year_in_t': [],
            }
        )

        self.factory._data_interface.production_unit_product_mapping = df

        result = self.factory._minimum_export_interpolation_data_in_t(1)

        # Verify result is empty dict
        assert result == {}
