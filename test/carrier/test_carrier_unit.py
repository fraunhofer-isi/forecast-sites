# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from carrier.carrier_unit import CarrierUnit


class TestCarrierUnit:
    """Test cases for CarrierUnit enum."""

    def test_carrier_unit_has_gj_and_t_values(self):
        """Test that CarrierUnit has expected enum values."""
        assert CarrierUnit.GJ.value == 1
        assert CarrierUnit.T.value == 2

    def test_carrier_unit_gj_uniqueness(self):
        """Test that GJ enum value is unique."""
        assert CarrierUnit.GJ != CarrierUnit.T

    def test_carrier_unit_t_uniqueness(self):
        """Test that T enum value is unique."""
        assert CarrierUnit.T != CarrierUnit.GJ

    def test_carrier_unit_enum_iteration(self):
        """Test that all carrier units can be iterated."""
        units = list(CarrierUnit)
        assert len(units) == 2
        assert CarrierUnit.GJ in units
        assert CarrierUnit.T in units

    def test_carrier_unit_name_access(self):
        """Test that enum names are accessible."""
        assert CarrierUnit.GJ.name == 'GJ'
        assert CarrierUnit.T.name == 'T'
