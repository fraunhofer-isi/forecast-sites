# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit pipeline cost methods."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitPipelineCost(unittest.TestCase):
    """Test ProductionUnit pipeline cost methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real methods
        self.mock_pu.pipeline_cost_scaling_factor = ProductionUnit.pipeline_cost_scaling_factor.__get__(self.mock_pu)
        self.mock_pu.pipeline_cost_in_euro = ProductionUnit.pipeline_cost_in_euro.__get__(self.mock_pu)

    def test_pipeline_cost_scaling_factor(self):
        """Test pipeline_cost_scaling_factor returns scaling from site context."""
        mock_site = mock.MagicMock()
        mock_site.pipeline_context = {'pipeline_cost_scaling_factor': 1.5}
        self.mock_pu._site = mock_site

        result = self.mock_pu.pipeline_cost_scaling_factor()

        assert result == 1.5

    def test_pipeline_cost_in_euro_no_sub_units(self):
        """Test pipeline_cost_in_euro with no sub-production units."""
        mock_site = mock.MagicMock()
        mock_site.pipeline_context = {'pipeline_cost_scaling_factor': 1.0}
        self.mock_pu._site = mock_site
        self.mock_pu.sub_production_units = []

        result = self.mock_pu.pipeline_cost_in_euro()

        assert result == 0

    def test_pipeline_cost_in_euro_with_sub_units(self):
        """Test pipeline_cost_in_euro sums costs from sub-production units."""
        mock_site = mock.MagicMock()
        mock_site.pipeline_context = {'pipeline_cost_scaling_factor': 2.0}
        self.mock_pu._site = mock_site

        mock_spu1 = mock.MagicMock()
        mock_spu1.pipeline_cost_in_euro.return_value = 100.0

        mock_spu2 = mock.MagicMock()
        mock_spu2.pipeline_cost_in_euro.return_value = 50.0

        self.mock_pu.sub_production_units = [mock_spu1, mock_spu2]

        result = self.mock_pu.pipeline_cost_in_euro()

        assert result == 150.0
        mock_spu1.pipeline_cost_in_euro.assert_called_once_with(2.0)
        mock_spu2.pipeline_cost_in_euro.assert_called_once_with(2.0)
