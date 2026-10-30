# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit.budget_relevant_emission_in_t_co2 method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitBudgetRelevantEmission(unittest.TestCase):
    """Test ProductionUnit.budget_relevant_emission_in_t_co2 method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_pu = mock.MagicMock(spec=ProductionUnit)
        # Call the real method
        self.mock_pu.budget_relevant_emission_in_t_co2 = ProductionUnit.budget_relevant_emission_in_t_co2.__get__(self.mock_pu)

    def test_budget_relevant_emission_empty_scope(self):
        """Test budget_relevant_emission_in_t_co2 with empty scope."""
        simulation_options = {'emission_constraint_scope': []}

        result = self.mock_pu.budget_relevant_emission_in_t_co2(2020, simulation_options)

        assert result == 0.0

    def test_budget_relevant_emission_direct_only(self):
        """Test budget_relevant_emission_in_t_co2 with direct emissions only."""
        self.mock_pu.upstream_emission_in_t_co2.return_value = {}
        self.mock_pu.renewably_bound_co2_emission_in_t_co2.return_value = {}
        self.mock_pu.downstream_emission_in_t_co2.return_value = {}

        mock_spu = mock.MagicMock()
        mock_spu.direct_emissions_in_t_co2.return_value = 100.0
        mock_spu.installed_process.emission.captured_emission_in_t_co2.return_value = 10.0

        self.mock_pu.sub_production_units = [mock_spu]

        simulation_options = {'emission_constraint_scope': ['direct']}

        result = self.mock_pu.budget_relevant_emission_in_t_co2(2020, simulation_options)

        assert result == 90.0  # 100 - 10

    def test_budget_relevant_emission_all_scopes(self):
        """Test budget_relevant_emission_in_t_co2 with all scopes."""
        self.mock_pu.upstream_emission_in_t_co2.return_value = {mock.MagicMock(): 50.0}
        self.mock_pu.renewably_bound_co2_emission_in_t_co2.return_value = {mock.MagicMock(): 20.0}
        self.mock_pu.downstream_emission_in_t_co2.return_value = {mock.MagicMock(): 30.0}

        mock_spu = mock.MagicMock()
        mock_spu.direct_emissions_in_t_co2.return_value = 100.0
        mock_spu.installed_process.emission.captured_emission_in_t_co2.return_value = 10.0

        self.mock_pu.sub_production_units = [mock_spu]

        simulation_options = {'emission_constraint_scope': ['direct', 'upstream', 'renewably_bound', 'downstream']}

        result = self.mock_pu.budget_relevant_emission_in_t_co2(2020, simulation_options)

        # 100 - 10 + 50 - 20 + 30 = 150
        assert result == 150.0
