# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.downstream_emission_in_t_co2 method."""

import unittest
from unittest import mock

import pytest

from production_unit.production_unit import ProductionUnit


class TestProductionUnitDownstreamEmission(unittest.TestCase):
    """Test ProductionUnit.downstream_emission_in_t_co2 method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.downstream_emission_in_t_co2 = ProductionUnit.downstream_emission_in_t_co2.__get__(self.mock_pu)

    def test_downstream_emission_empty_export(self):
        """Test downstream_emission_in_t_co2 with no export."""
        self.mock_pu.export.return_value = {}

        result = self.mock_pu.downstream_emission_in_t_co2(2020, {})

        assert result == {}

    def test_downstream_emission_with_carriers(self):
        """Test downstream_emission_in_t_co2 with exported carriers."""
        mock_carrier = mock.MagicMock()
        mock_carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.3

        self.mock_pu.export.return_value = {mock_carrier: 100.0}

        result = self.mock_pu.downstream_emission_in_t_co2(2020, {})

        assert mock_carrier in result
        assert result[mock_carrier] == 30.0  # 100 * 0.3

    def test_downstream_emission_negative_export_small(self):
        """Test downstream_emission_in_t_co2 with small negative export (numerical error)."""
        mock_carrier = mock.MagicMock()
        mock_carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.3

        self.mock_pu.export.return_value = {mock_carrier: -1e-4}

        result = self.mock_pu.downstream_emission_in_t_co2(2020, {})

        # Should normalize to 0 and not include in result
        assert mock_carrier not in result

    def test_downstream_emission_negative_export_large(self):
        """Test downstream_emission_in_t_co2 with large negative export (error)."""
        mock_carrier = mock.MagicMock()

        self.mock_pu.export.return_value = {mock_carrier: -1.0}

        with pytest.raises(ValueError, match='must not be negative'):
            self.mock_pu.downstream_emission_in_t_co2(2020, {})

    def test_downstream_emission_filters_carriers_without_method(self):
        """Test downstream_emission_in_t_co2 filters carriers without downstream_emission method."""
        mock_carrier_with_method = mock.MagicMock()
        mock_carrier_with_method.downstream_emission_in_t_co2_per_unit.return_value = 0.3

        mock_carrier_without_method = mock.MagicMock()
        del mock_carrier_without_method.downstream_emission_in_t_co2_per_unit

        self.mock_pu.export.return_value = {
            mock_carrier_with_method: 100.0,
            mock_carrier_without_method: 50.0,
        }

        result = self.mock_pu.downstream_emission_in_t_co2(2020, {})

        assert mock_carrier_with_method in result
        assert mock_carrier_without_method not in result
