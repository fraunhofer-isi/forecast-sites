# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from types import SimpleNamespace

from mesa_wrapper import mesa_server as mesa_server_module
from mesa_wrapper.mesa_server import MesaServer


class FakeSimulation:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.running = True
        self.step_calls = 0

    def step(self):
        self.step_calls += 1
        if self.step_calls >= 3:
            self.running = False


def test_run_headless_builds_simulation_and_steps_until_not_running(monkeypatch):
    created = []

    def create_simulation(**kwargs):
        simulation = FakeSimulation(**kwargs)
        created.append(simulation)
        return simulation

    monkeypatch.setattr(mesa_server_module, 'MesaSimulation', create_simulation)
    server = MesaServer(regions='regions', simulation_options={'headless': True}, visitors=['visitor'])

    server._run_headless()

    simulation = created[0]
    assert simulation.kwargs == {'regions': 'regions', 'options': {'headless': True}, 'visitors': ['visitor']}
    assert simulation.step_calls == 3


def test_primary_steel_colors_follow_last_matching_process():
    portrayal = MesaServer._set_color_for_primary_steel({}, [11, 39, 38])

    assert portrayal['color'] == 'Green'


def test_ammonia_colors_follow_last_matching_process():
    portrayal = MesaServer._set_color_for_ammonia({}, [9, 8])

    assert portrayal['color'] == 'Turquoise'


def test_olefins_colors_follow_last_matching_process():
    portrayal = MesaServer._set_color_for_olefins({}, [100, 44])

    assert portrayal['color'] == 'Purple'


def test_methanol_colors_follow_last_matching_process():
    portrayal = MesaServer._set_color_for_methanol({}, [60, 59])

    assert portrayal['color'] == 'Olive'


def test_data_collector_branch_reporters_count_agents_by_first_digit():
    collector = MesaServer._create_data_collector()
    simulation = SimpleNamespace(
        agents=[
            SimpleNamespace(used_process_ids=[11, 38]),
            SimpleNamespace(used_process_ids=[21]),
            SimpleNamespace(used_process_ids=[93]),
        ]
    )

    assert collector.model_reporters['Branch 1'](simulation) == 1
    assert collector.model_reporters['Branch 2'](simulation) == 1
    assert collector.model_reporters['Branch 9'](simulation) == 1
    assert collector.model_reporters['Branch 8'](simulation) == 0
