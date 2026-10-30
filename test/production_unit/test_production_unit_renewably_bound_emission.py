# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.renewably_bound_co2_emission_in_t_co2 method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitRenewablyBoundEmission(unittest.TestCase):
    """Test ProductionUnit.renewably_bound_co2_emission_in_t_co2 method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        method = ProductionUnit.renewably_bound_co2_emission_in_t_co2
        self.mock_pu.renewably_bound_co2_emission_in_t_co2 = method.__get__(self.mock_pu)

    def test_renewably_bound_emission_empty_purchased_carriers(self):
        """Test renewably_bound_co2_emission_in_t_co2 with no purchased carriers."""
        self.mock_pu.purchased_carrier_amounts = {}

        result = self.mock_pu.renewably_bound_co2_emission_in_t_co2(2020, {})

        assert result == {}

    def test_renewably_bound_emission_with_carriers(self):
        """Test renewably_bound_co2_emission_in_t_co2 with purchased carriers."""
        mock_carrier = mock.MagicMock()
        mock_carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.5

        self.mock_pu.purchased_carrier_amounts = {mock_carrier: 100.0}

        result = self.mock_pu.renewably_bound_co2_emission_in_t_co2(2020, {})

        assert mock_carrier in result
        assert result[mock_carrier] == 50.0  # 100 * 0.5
