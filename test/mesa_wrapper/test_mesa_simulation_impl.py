# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from types import SimpleNamespace

from mesa_wrapper.mesa_simulation import MesaSimulation
from optimization.optimization_type import OptimizationType


def test_initialize_start_year_uses_agent_step_when_optimization_enabled():
    calls = []
    visits = []
    simulation = MesaSimulation.__new__(MesaSimulation)
    simulation._time_span = [2030]
    simulation.steps = 0
    simulation.options = {
        'optimize_start_year': True,
        'optimization_type': OptimizationType.LINEAR_PROGRAMMING,
    }

    def do_action(action):
        calls.append(action)

    def accept_visitors(year):
        visits.append(year)

    simulation._all_agents = SimpleNamespace(do=do_action)
    simulation._accept_visitors = accept_visitors

    simulation._initialize_start_year()

    assert calls == ['step']
    assert visits == [2030]


def test_initialize_start_year_uses_region_optimization_when_type_is_region():
    calls = []
    visits = []
    simulation = MesaSimulation.__new__(MesaSimulation)
    simulation._time_span = [2030]
    simulation.steps = 0
    simulation.options = {
        'optimize_start_year': True,
        'optimization_type': OptimizationType.REGION_MULTI_PERIOD,
    }
    simulation._optimize_regions = calls.append
    simulation._accept_visitors = visits.append

    simulation._initialize_start_year()

    assert calls == [2030]
    assert visits == [2030]
