# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.new_investment_in_euro method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitNewInvestment(unittest.TestCase):
    """Test ProductionUnit.new_investment_in_euro method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.new_investment_in_euro = ProductionUnit.new_investment_in_euro.__get__(self.mock_pu)

    def test_new_investment_no_sub_units(self):
        """Test new_investment_in_euro with no sub-production units."""
        self.mock_pu.sub_production_units = []

        result = self.mock_pu.new_investment_in_euro(2020, {})

        assert result == 0

    def test_new_investment_with_sub_units(self):
        """Test new_investment_in_euro sums investments from sub-production units."""
        mock_spu1 = mock.MagicMock()
        mock_spu1.new_investment_in_euro.return_value = 1000.0

        mock_spu2 = mock.MagicMock()
        mock_spu2.new_investment_in_euro.return_value = 500.0

        self.mock_pu.sub_production_units = [mock_spu1, mock_spu2]

        result = self.mock_pu.new_investment_in_euro(2020, {})

        assert result == 1500.0
