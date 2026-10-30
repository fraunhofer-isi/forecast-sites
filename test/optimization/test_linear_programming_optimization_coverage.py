# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Targeted coverage tests for LinearProgrammingOptimization - missing branches.
Focus: Conditional branches and method return values (96% coverage)
"""

from unittest.mock import Mock

import pytest

from carrier.carrier_unit import CarrierUnit
from optimization.linear_programming_optimization import LinearProgrammingOptimization


class TestLinearProgrammingOptimizationCoverage:
    """Tests for missing branches in LinearProgrammingOptimization (96% coverage)"""

    def test_carrier_downstream_emission_without_attribute(self):
        """Test: Returns 0 when carrier lacks downstream_emission attribute"""
        carrier = Mock(spec=[])  # Spec with no attributes

        result = LinearProgrammingOptimization._carrier_downstream_emission_per_unit(carrier, 2025, {})

        assert result == 0.0

    def test_carrier_downstream_emission_with_attribute(self):
        """Test: Returns carrier value when attribute exists"""
        carrier = Mock()
        carrier.downstream_emission_in_t_co2_per_unit = Mock(return_value=0.75)

        result = LinearProgrammingOptimization._carrier_downstream_emission_per_unit(carrier, 2025, {})

        assert result == 0.75

    def test_minimum_export_for_gj_carrier(self):
        """Test: Minimum export for GJ unit returns 0"""
        context = Mock()
        context.simulation_options = {}
        context.interest_rate = 0.05

        opt = LinearProgrammingOptimization.__new__(LinearProgrammingOptimization)

        carrier = Mock(unit=CarrierUnit.GJ)
        result = opt._minimum_export(carrier, 2025, {})

        assert result == 0

    def test_minimum_export_for_unknown_unit(self):
        """Test: Unknown carrier unit raises TypeError"""
        context = Mock()
        context.simulation_options = {}
        context.interest_rate = 0.05

        opt = LinearProgrammingOptimization.__new__(LinearProgrammingOptimization)

        carrier = Mock(unit='UNKNOWN')

        with pytest.raises(TypeError, match='Unknown carrier unit'):
            opt._minimum_export(carrier, 2025, {})

    def test_constraints_to_linprog_format(self):
        """Test: Converts constraints to numpy format"""
        constraint1 = Mock()
        constraint1.matrix_coefficients = [1.0, 2.0, 3.0]
        constraint1.reference_value = 100.0

        constraint2 = Mock()
        constraint2.matrix_coefficients = [4.0, 5.0, 6.0]
        constraint2.reference_value = 200.0

        constraints = [constraint1, constraint2]

        coeff_matrix, coeff_vector = LinearProgrammingOptimization._constraints_to_linprog_format(constraints)

        assert coeff_matrix.shape == (2, 3)
        assert coeff_vector.shape == (2,)
        assert coeff_vector[0] == 100.0
        assert coeff_vector[1] == 200.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
