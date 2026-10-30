# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

from optimization.linear_programming_constraint import LinearProgrammingConstraint
from optimization.linear_programming_constraint_factory import LinearProgrammingConstraintFactory


class TestLinearProgrammingConstraintFactoryIntegration:
    """Integration tests for LinearProgrammingConstraintFactory."""

    def test_factory_workflow_create_and_configure(self) -> None:
        # Create a constraint for a typical optimization problem
        constraint = LinearProgrammingConstraintFactory.create_constraint(
            num_process_options=15,
            num_carriers=10,
            reference_value=500,
            label='energy_balance',
        )

        # Verify it was created correctly
        assert constraint.label == 'energy_balance'
        assert constraint.reference_value == 500

        # Now modify it (typical usage pattern)
        for i in range(5):
            constraint.process_option_coefficients[i] = i * 10

        # Verify modifications
        assert constraint.process_option_coefficients[0] == 0
        assert constraint.process_option_coefficients[1] == 10
        assert constraint.process_option_coefficients[4] == 40

    def test_factory_creates_constraints_for_optimization_system(self) -> None:
        # Simulate creating multiple constraints for a typical problem
        constraints = []

        # Energy balance constraints
        for carrier_id in range(5):
            constraint = LinearProgrammingConstraintFactory.create_constraint(
                num_process_options=20,
                num_carriers=5,
                reference_value=0,
                label=f'energy_balance_{carrier_id}',
            )
            constraints.append(constraint)

        # Emission constraints
        constraint = LinearProgrammingConstraintFactory.create_constraint(
            num_process_options=20,
            num_carriers=5,
            reference_value=1000,
            label='emission_limit',
        )
        constraints.append(constraint)

        # Verify all constraints were created
        assert len(constraints) == 6
        assert all(isinstance(c, LinearProgrammingConstraint) for c in constraints)

    def test_factory_constraint_properties_are_accessible(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100, label='test')

        # All properties should be accessible
        assert constraint.process_option_coefficients is not None
        assert constraint.carrier_coefficients is not None
        assert constraint.reference_value is not None
        assert constraint.label is not None
        assert constraint.matrix_coefficients is not None
