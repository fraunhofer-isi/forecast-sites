# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Factory for creating linear programming constraints."""

from optimization.linear_programming_constraint import LinearProgrammingConstraint


class LinearProgrammingConstraintFactory:
    """Factory for creating LinearProgrammingConstraint instances."""

    @staticmethod
    def create_constraint(num_process_options, num_carriers, reference_value, label=None):
        """
        Create a LinearProgrammingConstraint instance.

        Args:
            num_process_options: Number of process options (determines matrix size).
            num_carriers: Number of carriers (determines matrix size).
            reference_value: The right-hand side value of the constraint.
            label: Optional label for the constraint (e.g., 'production', 'emission').

        Returns:
            LinearProgrammingConstraint instance.

        """
        constraint = LinearProgrammingConstraint(
            num_process_options,
            num_carriers,
            reference_value,
            label,
        )
        return constraint
