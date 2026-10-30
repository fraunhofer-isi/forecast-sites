# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for CollectingResultVisitor budget summary handling."""

import unittest
from unittest import mock

from result.collecting_result_visitor import CollectingResultVisitor


class TestCollectingResultVisitorBudgetSummary(unittest.TestCase):
    """Test CollectingResultVisitor._collect_production_unit_overall_emission_budget method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_visitor = mock.MagicMock(spec=CollectingResultVisitor)
        # Call the real method
        self.mock_visitor._collect_production_unit_overall_emission_budget = (
            CollectingResultVisitor._collect_production_unit_overall_emission_budget.__get__(self.mock_visitor)
        )
        self.mock_visitor._simulation_options = {'start_year': 2020}
        self.mock_visitor._absolute_results = {}

    def test_collect_budget_with_none_summary(self):
        """Test _collect_production_unit_overall_emission_budget with None budget_summary."""
        mock_pu = mock.MagicMock()
        mock_pu.multi_period_budget_summary = None

        # Should return early without error
        result = self.mock_visitor._collect_production_unit_overall_emission_budget(2020, mock_pu)

        assert result is None

    def test_collect_budget_with_non_start_year(self):
        """Test _collect_production_unit_overall_emission_budget with non-start year."""
        mock_pu = mock.MagicMock()
        mock_pu.multi_period_budget_summary = {'used_in_t_co2': 100.0, 'available_in_t_co2': 200.0}

        # Should return early for non-start year
        result = self.mock_visitor._collect_production_unit_overall_emission_budget(2021, mock_pu)

        assert result is None
