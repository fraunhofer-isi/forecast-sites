# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit carrier tax and subsidy methods."""

import unittest
from unittest import mock

from carrier.carrier_unit import CarrierUnit
from production_unit.production_unit import ProductionUnit


class TestProductionUnitEnergyCarrierTaxes(unittest.TestCase):
    """Test ProductionUnit.energy_carrier_taxes_in_euro method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.energy_carrier_taxes_in_euro = ProductionUnit.energy_carrier_taxes_in_euro.__get__(self.mock_pu)

    def test_energy_carrier_taxes_empty_carriers(self):
        """Test energy_carrier_taxes_in_euro with no purchased carriers."""
        self.mock_pu.purchased_carrier_amounts = {}

        result = self.mock_pu.energy_carrier_taxes_in_euro(2020, {})

        assert result == {}

    def test_energy_carrier_taxes_with_gj_carriers(self):
        """Test energy_carrier_taxes_in_euro with GJ carriers."""
        mock_carrier = mock.MagicMock()
        mock_carrier.unit = CarrierUnit.GJ
        mock_carrier.taxes_in_euro_per_unit.return_value = 10.0

        self.mock_pu.purchased_carrier_amounts = {mock_carrier: 100.0}

        result = self.mock_pu.energy_carrier_taxes_in_euro(2020, {})

        assert mock_carrier in result
        assert result[mock_carrier] == 1000.0  # 10 * 100

    def test_energy_carrier_taxes_filters_non_gj_carriers(self):
        """Test energy_carrier_taxes_in_euro filters out non-GJ carriers."""
        mock_gj_carrier = mock.MagicMock()
        mock_gj_carrier.unit = CarrierUnit.GJ
        mock_gj_carrier.taxes_in_euro_per_unit.return_value = 10.0

        mock_t_carrier = mock.MagicMock()
        mock_t_carrier.unit = CarrierUnit.T

        self.mock_pu.purchased_carrier_amounts = {
            mock_gj_carrier: 100.0,
            mock_t_carrier: 50.0,
        }

        result = self.mock_pu.energy_carrier_taxes_in_euro(2020, {})

        assert mock_gj_carrier in result
        assert mock_t_carrier not in result
