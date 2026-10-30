# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for stateless carrier calculation logic."""

import pytest
from test_utils.isi_mock import Mock

from carrier.carrier_unit import CarrierUnit
from region.region_carrier_calculator import (
    RegionCarrierCalculator,
)


class TestDefaultCarrierAvailability:
    """Test carrier default availability calculation."""

    def test_default_availability_for_t_unit(self):
        """Test that T unit carriers get 0 availability."""
        carrier = Mock()
        carrier.unit = CarrierUnit.T
        carrier.name = 'coal'

        result = RegionCarrierCalculator.default_carrier_availability(carrier)
        assert result == 0

    def test_default_availability_for_gj_unit(self):
        """Test that GJ unit carriers get 10e10 availability."""
        carrier = Mock()
        carrier.unit = CarrierUnit.GJ
        carrier.name = 'electricity'

        result = RegionCarrierCalculator.default_carrier_availability(carrier)
        assert result == 10e10

    def test_default_availability_unknown_unit_raises_error(self):
        """Test that unknown carrier units raise TypeError."""
        carrier = Mock()
        carrier.unit = 'unknown_unit'
        carrier.name = 'test_carrier'

        with pytest.raises(TypeError, match='Unknown unit'):
            RegionCarrierCalculator.default_carrier_availability(carrier)


class TestValidatePurchasedAmount:
    """Test purchased carrier amount validation."""

    def test_valid_purchased_amount_zero(self):
        """Test that zero purchased amount is valid."""
        # Should not raise
        RegionCarrierCalculator.validate_purchased_amount(0)

    def test_valid_purchased_amount_positive(self):
        """Test that positive purchased amount is valid."""
        # Should not raise
        RegionCarrierCalculator.validate_purchased_amount(100)

    def test_valid_purchased_amount_within_tolerance(self):
        """Test that amount within negative tolerance is valid."""
        # NEGATIVE_TOLERANCE is -1e-5, so -1e-6 is within tolerance
        RegionCarrierCalculator.validate_purchased_amount(-1e-6)

    def test_invalid_purchased_amount_exceeds_tolerance(self):
        """Test that amount beyond negative tolerance raises ValueError."""
        # Note: NEGATIVE_TOLERANCE = -1e-3, so values >= -1e-3 are accepted (allows numerical precision errors)
        # Test with value clearly exceeding tolerance: -0.002 < -0.001 (tolerance)
        with pytest.raises(ValueError, match='never must be < 0'):
            RegionCarrierCalculator.validate_purchased_amount(-0.002)

    def test_invalid_purchased_amount_large_negative(self):
        """Test that large negative purchased amount raises ValueError."""
        with pytest.raises(ValueError, match='never must be < 0'):
            RegionCarrierCalculator.validate_purchased_amount(-1000)


class TestValidateProducedAmount:
    """Test produced carrier amount validation."""

    def test_valid_produced_amount_zero(self):
        """Test that zero produced amount is valid."""
        # Should not raise
        RegionCarrierCalculator.validate_produced_amount(0)

    def test_valid_produced_amount_positive(self):
        """Test that positive produced amount is valid."""
        # Should not raise
        RegionCarrierCalculator.validate_produced_amount(500)

    def test_invalid_produced_amount_negative(self):
        """Test that negative produced amount raises ValueError."""
        with pytest.raises(ValueError, match='never must be < 0'):
            RegionCarrierCalculator.validate_produced_amount(-0.1)

    def test_invalid_produced_amount_large_negative(self):
        """Test that large negative produced amount raises ValueError."""
        with pytest.raises(ValueError, match='never must be < 0'):
            RegionCarrierCalculator.validate_produced_amount(-5000)


class TestValidateCarrierKnown:
    """Test carrier existence validation."""

    def test_carrier_known_in_map(self):
        """Test that known carrier does not raise error."""
        carrier = Mock()
        carrier_map = {carrier: 100}

        # Should not raise
        RegionCarrierCalculator.validate_carrier_known(carrier, carrier_map)

    def test_carrier_unknown_raises_key_error(self):
        """Test that unknown carrier raises KeyError."""
        carrier = Mock()
        carrier_map = {}

        with pytest.raises(KeyError, match='not known in region'):
            RegionCarrierCalculator.validate_carrier_known(carrier, carrier_map)

    def test_carrier_with_other_carriers_in_map(self):
        """Test that carrier validation works with multiple carriers."""
        carrier1 = Mock()
        carrier2 = Mock()
        carrier_map = {carrier1: 50}

        with pytest.raises(KeyError, match='not known in region'):
            RegionCarrierCalculator.validate_carrier_known(carrier2, carrier_map)


class TestCheckAvailabilitySufficient:
    """Test availability sufficiency check."""

    def test_availability_exactly_matches_purchase(self):
        """Test that exact match returns True."""
        result = RegionCarrierCalculator.check_availability_sufficient(
            availability=100,
            purchased_amount=100,
        )
        assert result is True

    def test_availability_exceeds_purchase(self):
        """Test that excess availability returns True."""
        result = RegionCarrierCalculator.check_availability_sufficient(
            availability=150,
            purchased_amount=100,
        )
        assert result is True

    def test_availability_insufficient(self):
        """Test that insufficient availability returns False."""
        result = RegionCarrierCalculator.check_availability_sufficient(
            availability=50,
            purchased_amount=100,
        )
        assert result is False

    def test_availability_within_tolerance(self):
        """Test that shortage within tolerance returns True."""
        # Default tolerance is NEGATIVE_TOLERANCE (-1e-5)
        result = RegionCarrierCalculator.check_availability_sufficient(
            availability=100,
            purchased_amount=100.0000001,
        )
        assert result is True

    def test_availability_custom_tolerance(self):
        """Test that custom tolerance is respected."""
        result = RegionCarrierCalculator.check_availability_sufficient(
            availability=100,
            purchased_amount=100.1,
            tolerance=-0.2,
        )
        assert result is True

    def test_availability_zero_with_zero_purchase(self):
        """Test zero availability with zero purchase."""
        result = RegionCarrierCalculator.check_availability_sufficient(
            availability=0,
            purchased_amount=0,
        )
        assert result is True

    def test_availability_negative_tolerance_behavior(self):
        """Test that tolerance parameter allows small negatives."""
        # With a large tolerance, slightly negative difference is OK
        result = RegionCarrierCalculator.check_availability_sufficient(
            availability=99.99,
            purchased_amount=100,
            tolerance=-1,
        )
        assert result is True
