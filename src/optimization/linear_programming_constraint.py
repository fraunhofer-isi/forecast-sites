# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class LinearProgrammingConstraint:
    """
    Represents a single "row" of linear programming coefficients.

    A row consists of
    * a number of processes coefficients
    * a number of carrier coefficients
    * a reference value (right hand side of the equation)

    This structure allows for easier definition of the linear programming constraints in our context.

    All matrix coefficients (left side values) are initialized to 0.
    After initialization, the coefficients can be adapted as needed.

    The reference_value (right side value) is given as argument to the constructor and
    is typically not modified. (Only if you use copy of existing constraints and go from there to create a new one).
    """

    def __init__(
        self,
        number_of_process_options,
        number_of_carriers,
        reference_value,
        label=None,
    ):
        # first part of matrix coefficients
        self.process_option_coefficients = [0] * number_of_process_options

        # second part of matrix coefficients
        self.carrier_coefficients = [0] * number_of_carriers

        # right side value of the equation
        self.reference_value = reference_value

        # optional label for debugging
        self.label = label

    def __repr__(self):
        return (
            f'LinearProgrammingConstraint(||{self.process_option_coefficients}|{self.carrier_coefficients} ||'
            f'{self.reference_value}||{self.label})'
        )

    @property
    def matrix_coefficients(self):
        coefficients = self.process_option_coefficients + self.carrier_coefficients
        return coefficients
