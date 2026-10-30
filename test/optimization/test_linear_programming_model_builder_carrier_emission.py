# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for LinearProgrammingModelBuilder._carrier_emission_constraint_coefficient with downstream scope."""

import unittest
from unittest import mock

import pytest

from optimization.linear_programming_model_builder import LinearProgrammingModelBuilder


class TestCarrierEmissionConstraintCoefficientDownstream(unittest.TestCase):
    """Test _carrier_emission_constraint_coefficient with downstream scope."""

    def test_carrier_emission_with_downstream_scope(self):
        """Test carrier emission calculation includes downstream emissions."""
        # Setup
        mock_optimization = mock.MagicMock()
        builder = LinearProgrammingModelBuilder(mock_optimization)

        mock_carrier = mock.MagicMock()
        mock_carrier.upstream_emission_in_t_co2_per_unit.return_value = 5.0
        mock_carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 1.0
        mock_carrier.downstream_emission_in_t_co2_per_unit.return_value = 3.0

        simulation_options = {'emission_constraint_scope': ['upstream', 'renewably_bound', 'downstream']}

        result = builder._carrier_emission_constraint_coefficient(mock_carrier, 2020, simulation_options)

        # Expected: 5 - 1 + 3 = 7
        assert result == pytest.approx(7.0, abs=0.1)

    def test_carrier_emission_without_downstream_scope(self):
        """Test carrier emission calculation without downstream scope."""
        # Setup
        mock_optimization = mock.MagicMock()
        builder = LinearProgrammingModelBuilder(mock_optimization)

        mock_carrier = mock.MagicMock()
        mock_carrier.upstream_emission_in_t_co2_per_unit.return_value = 5.0
        mock_carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 1.0

        simulation_options = {'emission_constraint_scope': ['upstream', 'renewably_bound']}

        result = builder._carrier_emission_constraint_coefficient(mock_carrier, 2020, simulation_options)

        # Expected: 5 - 1 = 4 (no downstream)
        assert result == pytest.approx(4.0, abs=0.1)

    def test_carrier_emission_with_only_downstream_scope(self):
        """Test carrier emission with only downstream scope."""
        # Setup
        mock_optimization = mock.MagicMock()
        builder = LinearProgrammingModelBuilder(mock_optimization)

        mock_carrier = mock.MagicMock()
        mock_carrier.downstream_emission_in_t_co2_per_unit.return_value = 2.5

        simulation_options = {'emission_constraint_scope': ['downstream']}

        result = builder._carrier_emission_constraint_coefficient(mock_carrier, 2020, simulation_options)

        # Expected: 0 + 2.5 = 2.5
        assert result == pytest.approx(2.5, abs=0.1)
