# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from sector.sector import Sector


class TestSector:
    """Test the Sector class."""

    def test_sector_initialization(self):
        """Sector should initialize with id and name."""
        sector = Sector(id_sector=1, name='Manufacturing')
        assert sector.id == 1
        assert sector.name == 'Manufacturing'

    def test_sector_id_readonly(self):
        """Sector id should be read-only property."""
        sector = Sector(id_sector=1, name='Manufacturing')
        with pytest.raises(AttributeError):
            sector.id = 2

    def test_sector_repr(self):
        """Sector should have proper repr."""
        sector = Sector(id_sector=1, name='Manufacturing')
        assert repr(sector) == 'Sector(1, Manufacturing)'
