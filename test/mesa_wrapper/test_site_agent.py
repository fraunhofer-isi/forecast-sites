# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from mock import MagicMock, patch

from mesa_wrapper.site_agent import SiteAgent


@pytest.fixture
def sut():
    return SiteAgent(
        unique_id='mocked_id',
        model=MagicMock(),
        shape=MagicMock(),
        region_id=MagicMock(),
        site=MagicMock(),
    )


def test_step(sut):
    sut.step()
    # assert sut.model.regions.co2_cost_in_euro_per_ton_c02.called
    assert sut.site.process_year.called
    # assert sut.pipeline_cost_scaling.called
    # assert sut.get_distance_to_closest_H2_pipeline.called


def test__geo_interface__(sut):
    sut.model.grid.Transformer.transform = MagicMock()
    with patch('shapely.geometry.mapping', return_value='mocked_mapping'):
        result = sut.__geo_interface__()
        properties = result['properties']
        assert 'site' not in properties


# check tests from here onwards
def test_pipeline_cost_scaling(sut):
    distance_to_closest_h2_pipeline = 2
    result = sut.pipeline_cost_scaling(distance_to_closest_h2_pipeline)
    assert result == 200


def test_get_distance_to_closest_h2_pipeline(sut):
    sut.model.pipeline_site_relations = MagicMock()
    result = sut.model.pipeline_site_relations.indes.get_level_values()
    assert result.called
