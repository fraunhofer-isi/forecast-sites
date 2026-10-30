# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from types import SimpleNamespace

from optimization.linear_programming_optimization import LinearProgrammingOptimization


def test_production_constraints_use_zero_capacity_for_future_non_installed_process():
    optimization = LinearProgrammingOptimization.__new__(LinearProgrammingOptimization)
    process = SimpleNamespace(tech_available_at_year=2035)
    process_option = SimpleNamespace(process=process)
    constraint_calls = []

    optimization._production_unit = SimpleNamespace(available_process_options=[process_option], available_carriers=[])
    optimization._constraint = lambda reference_value, label=None: (
        constraint_calls.append((reference_value, label))
        or SimpleNamespace(
            process_option_coefficients=[0],
            carrier_coefficients=[],
            reference_value=reference_value,
            label=label,
        )
    )

    constraints = optimization._production_constraints(2030, {})

    assert len(constraints) == 1
    assert constraint_calls == [(0, 'production')]
    assert constraints[0].process_option_coefficients == [1]
