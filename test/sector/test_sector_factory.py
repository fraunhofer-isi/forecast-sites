# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pandas as pd
import pytest

from sector.sector import Sector
from sector.sector_factory import SectorFactory


class TestSectorFactory:
    """Test the SectorFactory class."""

    @pytest.fixture
    def mock_data_interface(self):
        """Create a mock data interface with test data."""
        data_interface = Mock()
        sector_data = pd.DataFrame({'id': [1, 2, 3], 'name': ['Manufacturing', 'Commerce', 'Households']})
        data_interface.sector_data = sector_data
        return data_interface

    def test_factory_initialization(self, mock_data_interface):
        """Should initialize with data interface."""
        factory = SectorFactory(mock_data_interface)
        assert factory is not None

    def test_create_map(self, mock_data_interface):
        """Should create map of sectors from data."""
        factory = SectorFactory(mock_data_interface)
        sector_map = factory.create_map()

        assert len(sector_map) == 3
        assert 1 in sector_map
        assert 2 in sector_map
        assert 3 in sector_map

    def test_create_map_returns_sector_objects(self, mock_data_interface):
        """Created sectors should be Sector instances."""
        factory = SectorFactory(mock_data_interface)
        sector_map = factory.create_map()

        assert isinstance(sector_map[1], Sector)
        assert isinstance(sector_map[2], Sector)
        assert isinstance(sector_map[3], Sector)

    def test_sector_names_correct(self, mock_data_interface):
        """Sectors should have correct names."""
        factory = SectorFactory(mock_data_interface)
        sector_map = factory.create_map()

        assert sector_map[1].name == 'Manufacturing'
        assert sector_map[2].name == 'Commerce'
        assert sector_map[3].name == 'Households'

    def test_sector_ids_correct(self, mock_data_interface):
        """Sectors should have correct IDs."""
        factory = SectorFactory(mock_data_interface)
        sector_map = factory.create_map()

        assert sector_map[1].id == 1
        assert sector_map[2].id == 2
        assert sector_map[3].id == 3

    def test_empty_sector_data(self):
        """Should handle empty sector data."""
        data_interface = Mock()
        data_interface.sector_data = pd.DataFrame({'id': [], 'name': []})

        factory = SectorFactory(data_interface)
        sector_map = factory.create_map()

        assert len(sector_map) == 0

    def test_single_sector(self):
        """Should handle single sector."""
        data_interface = Mock()
        data_interface.sector_data = pd.DataFrame({'id': [1], 'name': ['OnlySector']})

        factory = SectorFactory(data_interface)
        sector_map = factory.create_map()

        assert len(sector_map) == 1
        assert sector_map[1].name == 'OnlySector'
