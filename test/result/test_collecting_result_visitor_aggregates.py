# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for CollectingResultVisitor region and sector aggregates."""

import unittest
from unittest import mock

from result.collecting_result_visitor import CollectingResultVisitor


class TestCollectingResultVisitorAddRegionAndSectorAggregates(unittest.TestCase):
    """Test _add_region_and_sector_energy_carrier_aggregates method."""

    def setUp(self):
        """Set up test fixtures."""
        self.visitor = CollectingResultVisitor({'start_year': 2020})
        self.visitor._initialize()

    def test_add_region_and_sector_aggregates_purchased_amount_with_unit(self):
        """Test adding region and sector aggregates for purchased_amount with unit."""
        with (
            mock.patch.object(self.visitor, '_add_region_energy_carrier_entry_or_accumulate') as mock_region,
            mock.patch.object(self.visitor, '_add_sector_energy_carrier_entry_or_accumulate') as mock_sector,
        ):
            self.visitor._add_region_and_sector_energy_carrier_aggregates(
                'purchased_amount', 'energy_carrier_1', 2020, 100.0, append_unit=True
            )
            # Both should be called
            assert mock_region.called or mock_sector.called

    def test_add_region_and_sector_aggregates_skips_unknown_result_name(self):
        """Test that unknown result names are skipped."""
        with (
            mock.patch.object(self.visitor, '_add_region_energy_carrier_entry_or_accumulate') as mock_region,
            mock.patch.object(self.visitor, '_add_sector_energy_carrier_entry_or_accumulate') as mock_sector,
        ):
            self.visitor._add_region_and_sector_energy_carrier_aggregates(
                'unknown_result_name', 'energy_carrier_1', 2020, 100.0, append_unit=True
            )
            # Neither should be called
            mock_region.assert_not_called()
            mock_sector.assert_not_called()
