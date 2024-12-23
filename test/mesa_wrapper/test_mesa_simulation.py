# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from mesa.datacollection import DataCollector
from mesa_geo import AgentCreator
from mock import MagicMock, patch

from mesa_wrapper.mesa_simulation import MesaSimulation
from mesa_wrapper.time_schedule import TimeSchedule


def time_schedule_init_mock(self, model, time_span):
    self.step = MagicMock()
    self.time = 2020
    self.previous_time = None


def data_collector_init_mock(self, model_reporters=None, agent_reporters=None, tables=None):
    self.collect = MagicMock()


@pytest.fixture
def sut():
    with patch.object(TimeSchedule, '__init__', time_schedule_init_mock):
        with patch.object(DataCollector, '__init__', data_collector_init_mock):
            return MesaSimulation(
                simulation_mode='mocked_simulation_mode', time_span=[2020], regions=MagicMock(), visitors=[]
            )


class TestStep:

    def test_running(self, sut):
        visitor = MagicMock()
        sut._visitors = [visitor]

        sut.step()

        assert not visitor.finalize.called

    def test_not_running(self, sut):
        visitor = MagicMock()
        sut._visitors = [visitor]
        sut.running = False

        sut.step()

        assert visitor.finalize.called


def test_run(sut):
    sut.step = MagicMock()
    sut.run()
    assert sut.step.called


def test_year(sut):
    assert sut.year == 2020


def agent_creator_init_mock(self, agent_class, agent_kwargs, crs="epsg:3857"):
    self.create_agent = MagicMock()


@patch.object(AgentCreator, '__init__', agent_creator_init_mock)
def test__create_site_agents(sut):
    site_mock = MagicMock()
    sut.region.sites = [site_mock]

    sut.schedule.add = MagicMock()
    sut.grid.add_agents = MagicMock()

    sut._create_site_agents()

    assert sut.schedule.add.called
    assert sut.grid.add_agents.called


@patch.object(DataCollector, '__init__', data_collector_init_mock)
def test__create_data_collector(sut):
    result = sut._create_data_collector()
    assert result is not None


def test__determine_process_ids(sut):
    site_mock = MagicMock()
    site_mock.process_ids = 'mocked_process_ids'

    site_agent = MagicMock()
    site_agent.site = site_mock
    result = sut._determine_process_ids(site_agent)
    assert result == 'mocked_process_ids'


# Check tests from here onwards
def test_calculate_pipeline_site_distances(sut):
    site_mock = MagicMock()
    sut.region.sites = [site_mock]
    pipelines_mock = MagicMock()
    sut.pipeline.pipelines_df = [pipelines_mock]

    sut.pipeline_site_relations.loc = MagicMock()

    sut.calculate_pipline_site_distances()

    assert sut.pipeline_site_relations.loc.called


def test_calculate_km_distances(sut):
    sut.haversine_distance()

    sut.calculate_km_distance()
    assert sut.haversine_distance.called


def test_calculate_h2pipeline_site_distance(sut):
    site = MagicMock()
    pipeline = MagicMock()

    sut.calculate_pipeline_site_distance(site, pipeline)

    assert sut.calculate_km_distance().called


def test_update_pipelines(sut):
    sut.update_pipeline_site_relations()

    # Call the method under test
    sut.update_pipelines()

    # Assert that the necessary methods were called
    assert sut.pipelines.update_mode.called
    assert sut.update_pipeline_site_relations.called


def test_update_pipeline_site_relations():
    sut.pipeline_site_relations()

    # Call the method under test
    sut.update_pipeline_site_relations()

    # Assert that the necessary operations were performed
    assert sut.regions.values.called
    assert sut.pipelines.pipelines_df.iterrows.called
    assert sut.pipeline_site_relations.loc.called
