# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from mesa.datacollection import DataCollector
from mesa_viz_tornado.ModularVisualization import ModularServer
from mesa_viz_tornado.modules import ChartModule
from test_utils.isi_mock import Mock, patch

from mesa_wrapper.map_module import MapModule
from mesa_wrapper.mesa_server import MesaServer


def modular_server_init_mock(
    self,
    model_cls,
    _visualization_elements,
    _name,
    _model_params,
):
    self.model_cls = model_cls


@pytest.fixture
def sut():
    with patch(MesaServer._create_visualization_server):
        return MesaServer(
            'mocked_region',
            {'headless': False},
            [],
        )


def test_construction(sut):
    assert sut is not None


def test_run_launches_visualization_server(sut):
    mocked_launch = Mock()
    sut._visualization_server.launch = mocked_launch

    sut.run()

    assert mocked_launch.called


@patch(MesaServer._run_headless)
def test_run_in_headless_mode_calls_headless_runner():
    server = MesaServer('mocked_region', {'headless': True}, [])

    server.run()


def test_agent_portrayal_uses_first_matching_branch_color():
    mocked_site_agent = Mock(used_process_ids=[38, 81])

    result = MesaServer.agent_portrayal(mocked_site_agent)

    assert result == {'radius': '3', 'color': 'Green'}


def test_agent_portrayal_defaults_to_grey_when_no_branch_color_matches():
    mocked_site_agent = Mock(used_process_ids=[0])

    result = MesaServer.agent_portrayal(mocked_site_agent)

    assert result == {'radius': '3', 'color': 'Grey'}


def test_create_data_collector_returns_branch_reporters():
    result = MesaServer._create_data_collector()

    assert isinstance(result, DataCollector)
    assert 'agent_count' in result.model_reporters
    assert 'Branch 1' in result.model_reporters


@patch(ModularServer.__init__, modular_server_init_mock)
def test_create_visualization_server(sut):
    result = sut._create_visualization_server({})

    assert isinstance(result, ModularServer)


def test_create_visualization_elements(sut):
    result = sut._create_visualization_elements()

    assert len(result) == 2
    assert isinstance(result[0], MapModule)
    assert isinstance(result[1], ChartModule)
