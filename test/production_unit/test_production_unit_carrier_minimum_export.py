# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.carrier_minimum_export_in_t method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitCarrierMinimumExport(unittest.TestCase):
    """Test ProductionUnit.carrier_minimum_export_in_t method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.carrier_minimum_export_in_t = ProductionUnit.carrier_minimum_export_in_t.__get__(self.mock_pu)

    def test_carrier_minimum_export_no_data(self):
        """Test carrier_minimum_export_in_t with no interpolation data."""
        self.mock_pu._minimum_export_interpolation_data_in_t = {}
        mock_carrier = mock.MagicMock()

        result = self.mock_pu.carrier_minimum_export_in_t(mock_carrier, 2020, {})

        assert result == 0

    def test_carrier_minimum_export_with_data(self):
        """Test carrier_minimum_export_in_t with interpolation data."""
        mock_carrier = mock.MagicMock()
        interpolation_data = {2020: 50.0, 2030: 100.0}
        self.mock_pu._minimum_export_interpolation_data_in_t = {mock_carrier: interpolation_data}

        # Mock the interpolate function
        with mock.patch('production_unit.production_unit.interpolate', return_value=75.0):
            result = self.mock_pu.carrier_minimum_export_in_t(mock_carrier, 2025, {})

        assert result == 75.0
