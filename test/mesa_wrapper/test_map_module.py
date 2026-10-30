# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import json
from pathlib import Path

from test_utils.isi_mock import Mock, fixture, mock_open, patch

from mesa_wrapper.map_module import MapModule


@fixture
@patch(MapModule._initialize_view)
@patch(MapModule._javascript_code)
def sut():
    return MapModule(
        'mocked_simulation_options',
        'mocked_portrayal_method',
    )


def test_construction(sut):
    assert sut is not None


class TestInitializeView:
    def test_with_none(self):
        result = MapModule._initialize_view(None)
        assert result == [0, 0]

    def test_with_value(self):
        view = [1, 2]
        result = MapModule._initialize_view(view)
        assert result == view


@patch(Path.open, mock_open())
def test_store_feature_collection_as_json(sut):
    try:
        sut._store_feature_collection_as_json('mocked_feature_collection', 'mocked_file_path')
    except Exception as exception:
        message = f'_store_feature_collection_as_json raised an exception {exception}'
        raise AssertionError(message) from exception


def test_include_pipelines(sut):
    model = Mock()
    model.pipelines.pipelines_json = {'features': ['mocked_pipeline']}
    feature_collection = {'features': []}
    result = sut._include_pipelines(feature_collection, model)
    assert result == {'features': ['mocked_pipeline']}


@patch(MapModule._feature_collection, 'mocked_result')
@patch(MapModule._store_feature_collection_as_json)
@patch(json.dumps)
def test_render(sut):
    sut._simulation_options = {'output_directory': 'mocked_output_directory'}
    model = 'mocked_model'
    result = sut.render(model)

    assert result == 'mocked_result'


def test_javascript_code(sut):
    sut.view = 'mocked_view'
    result = sut._javascript_code(1, 2, 3)
    assert result == 'elements.push(new MapModule(mocked_view, 1, 3, 2));'


@patch(MapModule._include_pipelines)
@patch(MapModule._include_agents, 'mocked_result')
def test_feature_collection(sut):
    model = Mock()
    model.pipelines.pipelines_json = {'features': ['mocked_pipeline']}
    result = sut._feature_collection(model)
    assert result == 'mocked_result'


def test_include_agents(sut):
    sut.portrayal_method = Mock({'mocked_key': 'mocked_value'})

    model = Mock()

    mocked_shape = {'properties': {}}

    mocked_agent = Mock()
    mocked_agent.__geo_interface__ = Mock(mocked_shape)

    model.grid.agents = [mocked_agent]

    feature_collection = {'features': []}

    result = sut._include_agents(feature_collection, model)
    features = result['features']
    shape_info = features[0]
    properties = shape_info['properties']
    assert properties['mocked_key'] == 'mocked_value'
