# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnitFactory._filter_process_map_for_sector method."""

import unittest
from unittest import mock

from production_unit.production_unit_factory import ProductionUnitFactory


class TestProductionUnitFactoryFilterProcessMap(unittest.TestCase):
    """Test ProductionUnitFactory._filter_process_map_for_sector method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_data_interface = mock.MagicMock()
        self.mock_sub_pu_factory = mock.MagicMock()
        self.mock_sector_map = {}
        self.mock_process_map = {}
        self.mock_carriers = []
        self.mock_product_map = {}
        self.mock_optimization_factory = mock.MagicMock()
        self.mock_simulation_options = {}

        self.factory = ProductionUnitFactory(
            self.mock_data_interface,
            self.mock_sub_pu_factory,
            self.mock_sector_map,
            self.mock_process_map,
            self.mock_carriers,
            self.mock_product_map,
            self.mock_optimization_factory,
            self.mock_simulation_options,
        )

    def test_filter_includes_process_with_no_sector_filter(self):
        """Test filter includes process when no sector filter specified."""
        mock_process = mock.MagicMock()
        mock_process.sector_ids = []  # No sector filter

        self.mock_process_map[1] = mock_process

        result = self.factory._filter_process_map_for_sector(10)

        assert len(result) == 1
        assert 1 in result

    def test_filter_includes_process_with_matching_sector(self):
        """Test filter includes process when sector matches."""
        mock_process = mock.MagicMock()
        mock_process.sector_ids = [10, 20]  # Includes sector 10

        self.mock_process_map[1] = mock_process

        result = self.factory._filter_process_map_for_sector(10)

        assert len(result) == 1
        assert 1 in result

    def test_filter_excludes_process_with_non_matching_sector(self):
        """Test filter excludes process when sector doesn't match."""
        mock_process = mock.MagicMock()
        mock_process.sector_ids = [20, 30]  # Doesn't include sector 10

        self.mock_process_map[1] = mock_process

        result = self.factory._filter_process_map_for_sector(10)

        assert len(result) == 0

    def test_filter_with_mixed_processes(self):
        """Test filter with mix of matching and non-matching processes."""
        mock_process1 = mock.MagicMock()
        mock_process1.sector_ids = []  # No filter, include all

        mock_process2 = mock.MagicMock()
        mock_process2.sector_ids = [10]  # Matches sector 10

        mock_process3 = mock.MagicMock()
        mock_process3.sector_ids = [20]  # Doesn't match sector 10

        self.mock_process_map[1] = mock_process1
        self.mock_process_map[2] = mock_process2
        self.mock_process_map[3] = mock_process3

        result = self.factory._filter_process_map_for_sector(10)

        assert len(result) == 2
        assert 1 in result
        assert 2 in result
        assert 3 not in result

    def test_filter_empty_process_map(self):
        """Test filter with empty process map."""
        result = self.factory._filter_process_map_for_sector(10)

        assert len(result) == 0
