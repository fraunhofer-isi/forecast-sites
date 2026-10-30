# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Pure calculation logic for regional carrier availability and costs.

This module contains only stateless calculations for carrier management.
All methods are @staticmethod and require complete parameter passing.
"""

from carrier.carrier_unit import CarrierUnit

# Tolerance for numerical comparisons (small negative values are acceptable)
NEGATIVE_TOLERANCE = -1e-3


class RegionCarrierCalculator:
    """Stateless calculator for regional carrier operations."""

    @staticmethod
    def default_carrier_availability(carrier):
        """
        Calculate default carrier availability based on carrier unit type.

        Args:
            carrier: Carrier object with .unit attribute

        Returns:
            float: Availability (0 for T, 10e10 for GJ)

        Raises:
            TypeError: If carrier unit is unknown

        """
        carrier_unit = carrier.unit
        if carrier_unit == CarrierUnit.T:
            return 0
        if carrier_unit == CarrierUnit.GJ:
            return 10e10
        message = f'Unknown unit {carrier_unit} for carrier {carrier.name}'
        raise TypeError(message)

    @staticmethod
    def validate_purchased_amount(purchased_amount):
        """
        Validate that purchased carrier amount is non-negative.

        Args:
            purchased_amount: Amount being purchased

        Raises:
            ValueError: If amount is negative

        """
        if purchased_amount < NEGATIVE_TOLERANCE:
            msg = 'Purchased carrier amount never must be < 0.'
            raise ValueError(msg)

    @staticmethod
    def validate_produced_amount(produced_amount):
        """
        Validate that produced carrier amount is non-negative.

        Args:
            produced_amount: Amount being produced

        Raises:
            ValueError: If amount is negative

        """
        if produced_amount < 0:
            msg = 'Produced carrier amount never must be < 0.'
            raise ValueError(msg)

    @staticmethod
    def validate_carrier_known(carrier, carrier_availability_map):
        """
        Validate that carrier exists in availability map.

        Args:
            carrier: Carrier object
            carrier_availability_map: Dictionary of available carriers

        Raises:
            KeyError: If carrier not in map

        """
        if carrier not in carrier_availability_map:
            msg = 'Carrier not known in region. Query availability first.'
            raise KeyError(msg)

    @staticmethod
    def check_availability_sufficient(availability, purchased_amount, tolerance=NEGATIVE_TOLERANCE):
        """
        Check if availability is sufficient for purchase.

        Args:
            availability: Current availability amount
            purchased_amount: Amount being requested
            tolerance: Tolerance for negative values

        Returns:
            bool: True if availability >= purchased_amount (within tolerance)

        """
        return availability - purchased_amount >= tolerance
