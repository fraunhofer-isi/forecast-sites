# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
import shapely
from test_utils.isi_mock import Mock, original_patch, patch

from mesa_wrapper.site_agent import SiteAgent
from optimization.optimization_type import OptimizationType


@pytest.fixture
def sut():
    model = Mock()
    mocked_region = Mock()
    model.regions = {1: mocked_region}
    model.options = {'optimization_type': OptimizationType.LINEAR_PROGRAMMING}
    geometry = Mock()
    site = Mock()
    return SiteAgent(
        model,
        geometry,
        'epsg:4326',
        1,
        site,
    )


def test_construction(sut):
    assert sut is not None


def test_used_process_ids(sut):
    result = sut.used_process_ids
    assert result == sut._site.used_process_ids


def test_step(sut):
    sut.step()
    assert sut._site.optimize.called


def test_step_with_region_scoped_optimization():
    """Test that step returns early when optimization_type is region-scoped (line 34)."""
    model = Mock()
    mocked_region = Mock()
    model.regions = {1: mocked_region}
    model.options = {'optimization_type': OptimizationType.REGION_MULTI_PERIOD}  # Region-scoped
    geometry = Mock()
    site = Mock()

    sut = SiteAgent(
        model,
        geometry,
        'epsg:4326',
        1,
        site,
    )

    # When region-scoped, step should return early without calling optimize
    sut.step()

    # optimize should NOT be called when optimization is region-scoped
    assert not sut._site.optimize.called


@patch(shapely.ops.transform)
@original_patch('shapely.geometry.mapping', Mock('mocked_result'))
def test_geojson_geometry(sut):
    geometry = Mock()
    simulation = Mock()
    simulation.grid.transformer.transform = Mock()

    result = sut._geojson_geometry(geometry, simulation)
    assert result == 'mocked_result'


@patch(SiteAgent._properties, {'geometry': 'mocked_geometry'})
@patch(SiteAgent._geojson_geometry, 'mocked_geometry')
def test__geo_interface__(sut):
    result = sut.__geo_interface__()
    assert result['geometry'] == 'mocked_geometry'


def test_properties(sut):
    mocked_simulation = Mock()
    result = sut._properties(mocked_simulation)
    assert result['model'] == str(mocked_simulation)
