# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.sell_gain_in_euro method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitSellGain(unittest.TestCase):
    """Test ProductionUnit.sell_gain_in_euro method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.sell_gain_in_euro = ProductionUnit.sell_gain_in_euro.__get__(self.mock_pu)

    def test_sell_gain_no_carriers(self):
        """Test sell_gain_in_euro with no used carriers."""
        self.mock_pu.used_carriers = []

        result = self.mock_pu.sell_gain_in_euro(2020)

        assert result == {}

    def test_sell_gain_with_carriers(self):
        """Test sell_gain_in_euro with used carriers."""
        mock_carrier1 = mock.MagicMock()
        mock_carrier2 = mock.MagicMock()

        self.mock_pu.used_carriers = [mock_carrier1, mock_carrier2]
        self.mock_pu._sell_gain_in_euro_for_carrier = mock.MagicMock(side_effect=[100.0, 50.0])

        result = self.mock_pu.sell_gain_in_euro(2020)

        assert len(result) == 2
        assert result[mock_carrier1] == 100.0
        assert result[mock_carrier2] == 50.0
