# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from mesa_viz_tornado.ModularVisualization import ModularServer
from mesa_viz_tornado.modules import ChartModule
from mock import MagicMock, patch

from mesa_wrapper.map_module import MapModule
from mesa_wrapper.mesa_server import MesaServer
from mesa_wrapper.mesa_simulation import MesaSimulation


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
    with patch.object(ModularServer, '__init__', modular_server_init_mock):
        return MesaServer(
            simulation_mode='mocked_simulation_mode',
            time_span=[2020],
            regions='mocked_region',
            visitors=[],
        )


def test_run(sut):
    sut._visualization_server.launch = MagicMock()
    with patch('profile.run') as patched_profile_run:
        sut.run()
        assert patched_profile_run.called


class TestAgentPortrayal:

    site_mock = MagicMock()
    site_mock.process_ids = []

    site_agent = MagicMock()
    site_agent.site = site_mock

    def test_blue(self, sut):
        self.site_agent.site.process_ids = [39]
        result = sut.agent_portrayal(self.site_agent)
        assert result['color'] == 'Blue'

    def test_red(self, sut):
        self.site_agent.site.process_ids = [11]
        result = sut.agent_portrayal(self.site_agent)
        assert result['color'] == 'Red'

    def test_black(self, sut):
        self.site_agent.site.process_ids = [9]
        result = sut.agent_portrayal(self.site_agent)
        assert result['color'] == 'Black'

    def test_yellow(self, sut):
        self.site_agent.site.process_ids = [12]
        result = sut.agent_portrayal(self.site_agent)
        assert result['color'] == 'Yellow'

    def test_green(self, sut):
        self.site_agent.site.process_ids = [38]
        result = sut.agent_portrayal(self.site_agent)
        assert result['color'] == 'Green'

    def test_brown(self, sut):
        self.site_agent.site.process_ids = [100]
        result = sut.agent_portrayal(self.site_agent)
        assert result['color'] == 'Brown'

    def test_pink(self, sut):
        self.site_agent.site.process_ids = [8]
        result = sut.agent_portrayal(self.site_agent)
        assert result['color'] == 'Pink'


@patch.object(ModularServer, '__init__', modular_server_init_mock)
def test__create_visualization_server(sut):
    sut._create_visualization_elements = MagicMock()

    result = sut._create_visualization_server('mocked_model_params')

    assert sut._create_visualization_elements.called
    assert result.model_cls == MesaSimulation


def map_module_init_mock(
    self,
    _portrayal_method,
    _view,
    _zoom,
    _map_height,
    _map_width,
):
    pass


def chart_module_init_mock(
    self,
    _series,
    _canvas_height,
    _canvas_width,
    _data_collector_name,
):
    pass


@patch.object(MapModule, '__init__', map_module_init_mock)
@patch.object(ChartModule, '__init__', chart_module_init_mock)
def test__create_visualization_elements(sut):
    result = sut._create_visualization_elements()
    assert len(result) == 2
