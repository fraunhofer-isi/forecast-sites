# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnitFactory.create method."""

import unittest
from unittest import mock

import pandas as pd
import pytest

from production_unit.production_unit_factory import ProductionUnitFactory


class TestProductionUnitFactoryCreate(unittest.TestCase):
    """Test ProductionUnitFactory.create method."""

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

    def test_create_with_no_production_units_raises_error(self):
        """Test create raises ValueError when no production units found."""
        mock_site = mock.MagicMock()
        mock_site.id = 1

        # Empty DataFrame
        empty_df = pd.DataFrame()
        self.factory._site_production_unit_mapping = {1: empty_df}

        with pytest.raises(ValueError, match='No production units found'):
            self.factory.create(mock_site)

    def test_create_calls_create_production_unit_for_each_row(self):
        """Test create calls _create_production_unit for each production unit."""
        mock_site = mock.MagicMock()
        mock_site.id = 1

        # Create DataFrame with two production units
        df = pd.DataFrame({'id_sector': [10, 20]})
        df.index = [100, 101]

        self.factory._site_production_unit_mapping = {1: df}

        # Mock the _create_production_unit method
        mock_pu1 = mock.MagicMock()
        mock_pu2 = mock.MagicMock()
        self.factory._create_production_unit = mock.MagicMock(side_effect=[mock_pu1, mock_pu2])

        result = self.factory.create(mock_site)

        # Verify _create_production_unit was called twice
        assert self.factory._create_production_unit.call_count == 2
        assert len(result) == 2
        assert result[0] == mock_pu1
        assert result[1] == mock_pu2
