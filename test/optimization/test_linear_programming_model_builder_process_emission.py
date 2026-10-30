# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for LinearProgrammingModelBuilder._process_emission_constraint_coefficient with downstream scope."""

import unittest
from unittest import mock

import pytest

from optimization.linear_programming_model_builder import LinearProgrammingModelBuilder


class TestProcessEmissionConstraintCoefficientDownstream(unittest.TestCase):
    """Test _process_emission_constraint_coefficient with downstream scope."""

    def test_process_emission_with_downstream_scope(self):
        """Test process emission calculation includes downstream emissions."""
        # Setup
        mock_optimization = mock.MagicMock()
        builder = LinearProgrammingModelBuilder(mock_optimization)

        mock_process = mock.MagicMock()
        mock_process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 10.0
        mock_process.emission.captured_emission_in_t_co2_per_process_count = 2.0

        # Setup carriers with downstream emissions
        mock_carrier1 = mock.MagicMock()
        mock_carrier1.downstream_emission_in_t_co2_per_unit.return_value = 1.5
        mock_carrier2 = mock.MagicMock()
        mock_carrier2.downstream_emission_in_t_co2_per_unit.return_value = 2.5

        mock_optimization._carriers = [mock_carrier1, mock_carrier2]

        # Setup process netto amounts
        mock_process.netto_produced_or_consumed_amount_per_process_count.side_effect = [5.0, 3.0]

        simulation_options = {'emission_constraint_scope': ['direct', 'downstream']}

        result = builder._process_emission_constraint_coefficient(mock_process, 2020, simulation_options)

        # Expected: (10 - 2) + (5 * 1.5 + 3 * 2.5) = 8 + 7.5 + 7.5 = 23
        assert result == pytest.approx(23.0, abs=0.1)

    def test_process_emission_without_downstream_scope(self):
        """Test process emission calculation without downstream scope."""
        # Setup
        mock_optimization = mock.MagicMock()
        builder = LinearProgrammingModelBuilder(mock_optimization)

        mock_process = mock.MagicMock()
        mock_process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 10.0
        mock_process.emission.captured_emission_in_t_co2_per_process_count = 2.0

        mock_optimization._carriers = []

        simulation_options = {'emission_constraint_scope': ['direct']}

        result = builder._process_emission_constraint_coefficient(mock_process, 2020, simulation_options)

        # Expected: 10 - 2 = 8 (no downstream)
        assert result == pytest.approx(8.0, abs=0.1)

    def test_process_emission_without_direct_scope(self):
        """Test process emission calculation without direct scope (only downstream)."""
        # Setup
        mock_optimization = mock.MagicMock()
        builder = LinearProgrammingModelBuilder(mock_optimization)

        mock_process = mock.MagicMock()
        mock_process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 10.0
        mock_process.emission.captured_emission_in_t_co2_per_process_count = 2.0

        # Setup carriers with downstream emissions
        mock_carrier1 = mock.MagicMock()
        mock_carrier1.downstream_emission_in_t_co2_per_unit.return_value = 1.5
        mock_carrier2 = mock.MagicMock()
        mock_carrier2.downstream_emission_in_t_co2_per_unit.return_value = 2.5

        mock_optimization._carriers = [mock_carrier1, mock_carrier2]

        # Setup process netto amounts
        mock_process.netto_produced_or_consumed_amount_per_process_count.side_effect = [5.0, 3.0]

        simulation_options = {
            'emission_constraint_scope': ['downstream']  # No 'direct'
        }

        result = builder._process_emission_constraint_coefficient(mock_process, 2020, simulation_options)

        # Expected: 0 (no direct) + (5 * 1.5 + 3 * 2.5) = 7.5 + 7.5 = 15
        assert result == pytest.approx(15.0, abs=0.1)
