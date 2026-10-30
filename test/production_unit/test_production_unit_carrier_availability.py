# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.carrier_availability method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitCarrierAvailability(unittest.TestCase):
    """Test ProductionUnit.carrier_availability method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.carrier_availability = ProductionUnit.carrier_availability.__get__(self.mock_pu)

    def test_carrier_availability_delegates_to_site(self):
        """Test carrier_availability delegates to site."""
        mock_site = mock.MagicMock()
        mock_site.carrier_availability.return_value = 100.0
        self.mock_pu._site = mock_site

        mock_carrier = mock.MagicMock()

        result = self.mock_pu.carrier_availability(mock_carrier, 2020)

        assert result == 100.0
        mock_site.carrier_availability.assert_called_once_with(mock_carrier, 2020)
