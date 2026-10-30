# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.products property."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitProducts(unittest.TestCase):
    """Test ProductionUnit.products property."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)

    def test_products_empty(self):
        """Test products with no minimum export data."""
        self.mock_pu._minimum_export_interpolation_data_in_t = {}

        result = ProductionUnit.products.fget(self.mock_pu)

        assert result == []

    def test_products_with_data(self):
        """Test products returns keys from minimum export data."""
        mock_product1 = mock.MagicMock()
        mock_product2 = mock.MagicMock()

        self.mock_pu._minimum_export_interpolation_data_in_t = {
            mock_product1: {2020: 50.0},
            mock_product2: {2020: 100.0},
        }

        result = ProductionUnit.products.fget(self.mock_pu)

        assert len(result) == 2
        assert mock_product1 in result
        assert mock_product2 in result
