# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnitFactory._create_production_unit method."""

import unittest
from unittest import mock

import pandas as pd

from production_unit.production_unit_factory import ProductionUnitFactory


class TestProductionUnitFactoryCreateProductionUnit(unittest.TestCase):
    """Test ProductionUnitFactory._create_production_unit method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_data_interface = mock.MagicMock()
        self.mock_sub_pu_factory = mock.MagicMock()
        self.mock_sector_map = {}
        self.mock_process_map = {}
        self.mock_carriers = []
        self.mock_product_map = {}
        self.mock_optimization_factory = mock.MagicMock()
        self.mock_simulation_options = {'start_year': 2020}

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

    def test_create_production_unit_with_minimum_export_data(self):
        """Test _create_production_unit creates ProductionUnit with minimum export data."""
        mock_site = mock.MagicMock()
        mock_sector = mock.MagicMock()
        self.factory._sector_map = {10: mock_sector}

        # Create a row with id_sector
        row = pd.Series({'id_sector': 10})
        row.name = 100  # id_production_unit

        # Mock the helper methods
        mock_interpolation_data = mock.MagicMock()
        self.factory._minimum_export_interpolation_data_in_t = mock.MagicMock(return_value=mock_interpolation_data)
        self.factory._filter_process_map_for_sector = mock.MagicMock(return_value={})

        result = self.factory._create_production_unit(mock_site, row)

        # Verify the helper methods were called
        self.factory._minimum_export_interpolation_data_in_t.assert_called_once_with(100)
        self.factory._filter_process_map_for_sector.assert_called_once_with(10)

        # Verify a ProductionUnit was created
        assert result is not None
