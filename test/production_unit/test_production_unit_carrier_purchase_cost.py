# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.carrier_purchase_cost_in_euro method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitCarrierPurchaseCost(unittest.TestCase):
    """Test ProductionUnit.carrier_purchase_cost_in_euro method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.carrier_purchase_cost_in_euro = ProductionUnit.carrier_purchase_cost_in_euro.__get__(self.mock_pu)

    def test_carrier_purchase_cost_no_carriers(self):
        """Test carrier_purchase_cost_in_euro with no purchased carriers."""
        self.mock_pu.purchased_carrier_amounts = {}

        result = self.mock_pu.carrier_purchase_cost_in_euro(2020)

        assert result == {}

    def test_carrier_purchase_cost_with_carriers(self):
        """Test carrier_purchase_cost_in_euro with purchased carriers."""
        mock_carrier = mock.MagicMock()
        mock_carrier.purchase_cost_in_euro.return_value = 50.0

        self.mock_pu.purchased_carrier_amounts = {mock_carrier: 100.0}

        result = self.mock_pu.carrier_purchase_cost_in_euro(2020)

        assert mock_carrier in result
        assert result[mock_carrier] == 50.0
        mock_carrier.purchase_cost_in_euro.assert_called_once_with(100.0, 2020)
