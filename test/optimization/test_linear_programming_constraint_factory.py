# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

from optimization.linear_programming_constraint import LinearProgrammingConstraint
from optimization.linear_programming_constraint_factory import LinearProgrammingConstraintFactory


class TestCreateConstraint:
    """Tests for LinearProgrammingConstraintFactory.create_constraint method."""

    def test_create_constraint_returns_instance(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100)

        assert isinstance(constraint, LinearProgrammingConstraint)

    def test_create_constraint_with_default_label(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100)

        assert constraint.label is None

    def test_create_constraint_with_custom_label(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100, label='production')

        assert constraint.label == 'production'

    def test_create_constraint_sets_process_options(self) -> None:
        num_processes = 10
        constraint = LinearProgrammingConstraintFactory.create_constraint(num_processes, 5, 100)

        assert len(constraint.process_option_coefficients) == num_processes

    def test_create_constraint_sets_carriers(self) -> None:
        num_carriers = 5
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, num_carriers, 100)

        assert len(constraint.carrier_coefficients) == num_carriers

    def test_create_constraint_sets_reference_value(self) -> None:
        reference_value = 100
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, reference_value)

        assert constraint.reference_value == reference_value

    def test_create_constraint_with_zero_reference_value(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 0)

        assert constraint.reference_value == 0

    def test_create_constraint_with_negative_reference_value(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, -50)

        assert constraint.reference_value == -50

    def test_create_constraint_with_large_reference_value(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 1000000)

        assert constraint.reference_value == 1000000

    def test_create_constraint_with_float_reference_value(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100.5)

        assert constraint.reference_value == 100.5

    def test_create_constraint_initializes_coefficients_to_zero(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100)

        assert all(c == 0 for c in constraint.process_option_coefficients)
        assert all(c == 0 for c in constraint.carrier_coefficients)

    def test_create_constraint_with_single_process(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(1, 5, 100)

        assert len(constraint.process_option_coefficients) == 1
        assert constraint.process_option_coefficients[0] == 0

    def test_create_constraint_with_single_carrier(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 1, 100)

        assert len(constraint.carrier_coefficients) == 1
        assert constraint.carrier_coefficients[0] == 0

    def test_create_constraint_with_large_matrix_dimensions(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(1000, 500, 100)

        assert len(constraint.process_option_coefficients) == 1000
        assert len(constraint.carrier_coefficients) == 500

    def test_create_constraint_with_empty_processes(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(0, 5, 100)

        assert len(constraint.process_option_coefficients) == 0

    def test_create_constraint_with_empty_carriers(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 0, 100)

        assert len(constraint.carrier_coefficients) == 0

    def test_create_constraint_with_both_empty(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(0, 0, 100)

        assert len(constraint.process_option_coefficients) == 0
        assert len(constraint.carrier_coefficients) == 0

    def test_create_constraint_matrix_coefficients_property(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(3, 2, 100)

        expected_length = 3 + 2
        assert len(constraint.matrix_coefficients) == expected_length

    def test_create_constraint_label_variants(self) -> None:
        """Test various label values."""
        labels = ['production', 'emission', 'cost', 'energy_balance', 'constraint_1']

        for label in labels:
            constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100, label=label)
            assert constraint.label == label

    def test_create_constraint_with_empty_string_label(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100, label='')

        assert constraint.label == ''

    def test_create_constraint_static_method(self) -> None:
        """Verify create_constraint is a static method."""
        # Should be callable without instance
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100)

        assert constraint is not None

    def test_create_multiple_constraints_are_independent(self) -> None:
        constraint1 = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100, label='c1')
        constraint2 = LinearProgrammingConstraintFactory.create_constraint(20, 8, 200, label='c2')

        assert constraint1.label == 'c1'
        assert constraint2.label == 'c2'
        assert len(constraint1.process_option_coefficients) == 10
        assert len(constraint2.process_option_coefficients) == 20

    def test_create_constraint_can_be_modified_after_creation(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(10, 5, 100, label='test')

        # Modify the constraint
        constraint.process_option_coefficients[0] = 1.5
        constraint.carrier_coefficients[0] = 2.5
        constraint.reference_value = 200

        # Verify modifications stick
        assert constraint.process_option_coefficients[0] == 1.5
        assert constraint.carrier_coefficients[0] == 2.5
        assert constraint.reference_value == 200

    def test_create_constraint_repr(self) -> None:
        constraint = LinearProgrammingConstraintFactory.create_constraint(2, 2, 100, label='test')

        repr_str = repr(constraint)

        assert 'LinearProgrammingConstraint' in repr_str
        assert '100' in repr_str
        assert 'test' in repr_str
