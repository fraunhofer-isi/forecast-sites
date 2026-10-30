# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from mesa.datacollection import DataCollector
from mesa_geo import AgentCreator
from pandas import DataFrame, RangeIndex, Series
from test_utils.isi_mock import Mock, fixture, patch

from mesa_wrapper.mesa_simulation import MesaSimulation
from optimization.optimization_type import OptimizationType
from pipelines.pipelines import Pipelines
from utils import geometry_utils


@fixture
@patch(MesaSimulation._create_time_span, [2020, 2021])
@patch(MesaSimulation._create_data_collector)
@patch(Pipelines.__init__, None)
@patch(MesaSimulation._pipeline_site_relations)
@patch(MesaSimulation._initialize_start_year)
def sut():
    return MesaSimulation(
        Mock(),
        {
            'optimize_start_year': False,
            'optimization_type': OptimizationType.LINEAR_PROGRAMMING,
        },
        [],
    )


def test_construction(sut):
    assert sut is not None


@patch(MesaSimulation._update_pipelines)
@patch(MesaSimulation._accept_visitors)
@patch(MesaSimulation._end_simulation_after_last_year)
@patch(MesaSimulation._finalize_visitors_if_finished)
def test_step(sut):
    visitor = Mock()
    sut._visitors = [visitor]

    sut.step()

    assert not visitor.finalize.called


@patch(MesaSimulation._create_site_agents)
@patch(MesaSimulation._consume_purchased_carrier_amounts_for_start_year)
@patch(MesaSimulation._accept_visitors)
def test_initialize_start_year(sut):
    sut._initialize_start_year()


def test_consume_purchased_carrier_amounts_for_start_year(sut):
    mocked_region = Mock()
    sut.regions = {1: mocked_region}
    sut._consume_purchased_carrier_amounts_for_start_year(2020)
    assert mocked_region.consume_purchased_carrier_amounts_for_start_year.called


# provide_produced_carrier_amounts_for_start_year removed - test deleted


def test_year(sut):
    result = sut.year
    assert result == 2020


def test_last_year(sut):
    result = sut._last_year
    assert result == 2021


def test_create_data_collector(sut):
    result = sut._create_data_collector()
    result.model_reporters['agent_count'](Mock())
    result.agent_reporters['process_ids'](Mock())
    assert isinstance(result, DataCollector)


def test_create_time_span(sut):
    sut.options = {
        'start_year': 2020,
        'end_year': 2022,
        'year_increment': 2,
    }
    result = sut._create_time_span()
    assert result == [2020, 2022]


def test_accept_visitors(sut):
    sut._visitors = ['mocked_visitor']

    mocked_region = Mock()
    sut.regions = {1: mocked_region}

    sut._accept_visitors(2020)

    assert mocked_region.accept.called


def test_finalize_visitors_if_finished(sut):
    sut.running = False
    mocked_visitor = Mock()
    sut._visitors = [mocked_visitor]
    sut._finalize_visitors_if_finished()

    assert mocked_visitor.finalize.called


def test_finalize_visitors_if_not_finished(sut):
    """Test that finalize is not called when simulation is still running."""
    sut.running = True
    mocked_visitor = Mock()
    sut._visitors = [mocked_visitor]
    sut._finalize_visitors_if_finished()

    assert not mocked_visitor.finalize.called


def agent_creator_init_mock(
    self,
    agent_class,
    model=None,
    crs=None,
    agent_kwargs=None,
):
    self.agent_class = agent_class
    self.model = model
    self.crc = crs
    self.agent_kwargs = agent_kwargs
    self.create_agent = Mock()


@patch(AgentCreator.__init__, agent_creator_init_mock)
def test_create_site_agents(sut):
    mocked_region = Mock()
    mocked_region.sites = [Mock()]

    sut.regions = {1: mocked_region}
    sut.grid = Mock()

    sut._create_site_agents()

    assert sut.grid.add_agents.called


class TestPipelineSiteRelations:
    def test_not_recognizing(self, sut):
        sut.is_recognizing_pipelines = False
        result = sut._pipeline_site_relations()
        assert result is None

    @patch(MesaSimulation._site_ids, [1])
    @patch(MesaSimulation._determine_pipeline_site_distances_in_km, 'mocked_result')
    def test_recognizing(self, sut):
        sut.is_recognizing_pipelines = True
        sut.pipelines = Mock()
        sut.pipelines.pipeline_indices = RangeIndex(1, 3)
        result = sut._pipeline_site_relations()
        assert result == 'mocked_result'


def test_end_simulation_after_last_year(sut):
    sut._end_simulation_after_last_year(2020)
    assert sut.running

    sut._end_simulation_after_last_year(2021)
    assert not sut.running


def test_site_ids(sut):
    mocked_site = Mock()
    mocked_site.id = 33

    mocked_region = Mock()
    mocked_region.sites = [mocked_site]
    sut.regions = {1: mocked_region}

    result = sut._site_ids()
    assert result == [33]


def test_determine_pipeline_site_distances(sut):
    # Patch the method on the instance itself
    sut._calculate_pipeline_site_distance_in_km = Mock(return_value=42)

    mocked_site = Mock()
    mocked_site.id = 33

    mocked_region = Mock()
    mocked_region.sites = [mocked_site]
    sut.regions = {1: mocked_region}

    sut.pipelines = Mock()
    sut.pipelines.pipelines_df = DataFrame([{'id': 1}])

    pipeline_site_relations = DataFrame([{'site': 33, 'pipeline': 1, 'distance': 0}]).set_index(['site', 'pipeline'])

    result = sut._determine_pipeline_site_distances_in_km(pipeline_site_relations)
    relation = result.loc[(33, 1)]
    assert relation['distance'] == 42


@patch(MesaSimulation._haversine_distance_in_km, 'mocked_result')
def test_calculate_km_distances(sut):
    site = Mock()
    line = Mock()

    result = sut._calculate_km_distance(site, line)
    assert result == 'mocked_result'


def test_haversine_distance_in_km(sut):
    result = sut._haversine_distance_in_km(50, 10, 50, 10)
    assert result == 0

    result = sut._haversine_distance_in_km(0, 0, 0, 0.9)
    assert result == pytest.approx(100, 0.1)


@patch(geometry_utils.remove_duplicate_points)
@patch(MesaSimulation._calculate_km_distance, 100)
def test_calculate_pipeline_site_distance(sut):
    sut.pipelines.file_path = 'some/data/file.geojson'
    site = Mock()
    mocked_geometry = Mock()
    mocked_geometry.geoms = ['mocked_line']
    pipeline_row = Series({'id': 1, 'geometry': mocked_geometry})

    result = sut._calculate_pipeline_site_distance_in_km(site, pipeline_row)
    assert result == 100

    assert sut._calculate_km_distance.called


def test_update_pipelines(sut):
    sut.pipelines = Mock()
    sut._update_pipeline_site_relations = Mock()

    sut.is_recognizing_pipelines = False
    sut._update_pipelines()
    assert not sut.pipelines.update_modes.called

    sut.is_recognizing_pipelines = True
    sut._update_pipelines()
    assert sut.pipelines.update_modes.called
    assert sut._update_pipeline_site_relations.called


def test_update_pipeline_site_relations(sut):
    mocked_site = Mock()
    mocked_site.id = 33

    mocked_region = Mock()
    mocked_region.sites = [mocked_site]
    sut.regions = {1: mocked_region}

    sut.pipeline_site_relations = DataFrame([{'site': 33, 'pipeline': 1, 'distance': 0, 'mode': ''}]).set_index(
        ['site', 'pipeline']
    )

    sut.pipelines = Mock()
    sut.pipelines.pipelines_df = DataFrame([{'id': 1, 'mode': 'H2'}])

    sut._update_pipeline_site_relations()

    relation = sut.pipeline_site_relations.loc[33, 1]
    assert relation['mode'] == 'H2'


class TestRegionScopedOptimization:
    """Tests for region-scoped optimization paths."""

    @patch(MesaSimulation._optimize_regions)
    @patch(MesaSimulation._update_pipelines)
    @patch(MesaSimulation._accept_visitors)
    @patch(MesaSimulation._end_simulation_after_last_year)
    @patch(MesaSimulation._finalize_visitors_if_finished)
    @patch(MesaSimulation._create_time_span, [2020, 2021])
    @patch(MesaSimulation._create_data_collector)
    @patch(Pipelines.__init__, None)
    @patch(MesaSimulation._pipeline_site_relations)
    @patch(MesaSimulation._initialize_start_year)
    def test_step_with_region_scoped_optimization(self):
        """Test step method with region-scoped optimization enabled."""
        options = {
            'optimize_start_year': False,
            'optimization_type': OptimizationType.REGION_MULTI_PERIOD,
        }
        sut = MesaSimulation(Mock(), options, [])

        sut.step()

        assert sut._optimize_regions.called

    @patch(MesaSimulation._optimize_regions)
    @patch(MesaSimulation._consume_purchased_carrier_amounts_for_start_year)
    @patch(MesaSimulation._accept_visitors)
    @patch(MesaSimulation._create_site_agents)
    @patch(MesaSimulation._create_time_span, [2020, 2021])
    @patch(MesaSimulation._create_data_collector)
    @patch(Pipelines.__init__, None)
    @patch(MesaSimulation._pipeline_site_relations)
    def test_initialize_start_year_with_region_scoped_optimization(self):
        """Test _initialize_start_year with region-scoped optimization enabled."""
        options = {
            'optimize_start_year': True,
            'optimization_type': OptimizationType.REGION_MULTI_PERIOD,
        }
        sut = MesaSimulation(Mock(), options, [])

        sut._initialize_start_year()

        assert sut._optimize_regions.called

    @patch(MesaSimulation._create_time_span, [2020, 2021])
    @patch(MesaSimulation._create_data_collector)
    @patch(Pipelines.__init__, None)
    @patch(MesaSimulation._pipeline_site_relations)
    @patch(MesaSimulation._initialize_start_year)
    def test_optimize_regions(self):
        """Test _optimize_regions method calls region optimize for each region."""
        options = {
            'optimization_type': OptimizationType.REGION_MULTI_PERIOD,
        }
        sut = MesaSimulation(Mock(), options, [])

        # Create mocked region and site
        mocked_site = Mock()
        mocked_site.initialize_context = Mock()
        mocked_site._optimization_context = Mock()

        mocked_region = Mock()
        mocked_region.sites = [mocked_site]
        mocked_region.optimize = Mock()

        sut.regions = {1: mocked_region}

        sut._optimize_regions(2020)

        assert mocked_site.initialize_context.called
        assert mocked_region.optimize.called

    def test_step_finalization_logic(self, sut):
        """Test that finalization logic works when not running."""
        sut.running = False
        mocked_visitor = Mock()
        sut._visitors = [mocked_visitor]

        sut._finalize_visitors_if_finished()

        assert mocked_visitor.finalize.called

    def test_end_simulation_sets_running_to_false_at_last_year(self, sut):
        """Test that running flag is set to False at last year."""
        sut._end_simulation_after_last_year(sut._last_year)

        assert not sut.running

    @patch(MesaSimulation._optimize_regions)
    @patch(MesaSimulation._update_pipelines)
    @patch(MesaSimulation._accept_visitors)
    @patch(MesaSimulation._finalize_visitors_if_finished)
    @patch(MesaSimulation._create_time_span, [2020, 2021])
    @patch(MesaSimulation._create_data_collector)
    @patch(Pipelines.__init__, None)
    @patch(MesaSimulation._pipeline_site_relations)
    @patch(MesaSimulation._initialize_start_year)
    def test_step_does_not_call_optimize_regions_for_non_region_scoped(self):
        """Test step method skips _optimize_regions for non-region-scoped optimization."""
        options = {
            'optimize_start_year': False,
            'optimization_type': OptimizationType.LINEAR_PROGRAMMING,
        }
        sut = MesaSimulation(Mock(), options, [])

        sut.step()

        # Should not have called optimize_regions when not region-scoped
        assert not sut._optimize_regions.called
