# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.number_of_process_usages method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitNumberOfProcessUsages(unittest.TestCase):
    """Test ProductionUnit.number_of_process_usages method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.number_of_process_usages = ProductionUnit.number_of_process_usages.__get__(self.mock_pu)

    def test_number_of_process_usages_no_sub_units(self):
        """Test number_of_process_usages with no sub-production units."""
        self.mock_pu.sub_production_units = []
        mock_process = mock.MagicMock()

        result = self.mock_pu.number_of_process_usages(mock_process)

        assert result == 0

    def test_number_of_process_usages_with_sub_units(self):
        """Test number_of_process_usages with sub-production units."""
        mock_spu1 = mock.MagicMock()
        mock_spu1.number_of_process_usages.return_value = 2

        mock_spu2 = mock.MagicMock()
        mock_spu2.number_of_process_usages.return_value = 3

        self.mock_pu.sub_production_units = [mock_spu1, mock_spu2]
        mock_process = mock.MagicMock()

        result = self.mock_pu.number_of_process_usages(mock_process)

        assert result == 5  # 2 + 3
