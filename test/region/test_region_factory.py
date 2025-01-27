# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from data_interface import DataInterface
from region.region import Region
from region.region_factory import RegionFactory
from test_utils.isi_mock import MagicMock, patch


def data_interface_init_mock(
    self,
    _id_scenario,
    _scenario_options,
    _id_region,
):
    pass


def region_init_mock(
    self,
    _region_id,
    _data_interface,
):
    self.id = None
    self._sites = [MagicMock(), MagicMock]
    self.accept = MagicMock()


@pytest.fixture
def sut():
    mocked_scenario_options = {'region_ids': [1, 2]}
    region_factory = RegionFactory('mocked_id_scenario', mocked_scenario_options)
    return region_factory


@patch(RegionFactory._create_region, 'MockedRegion')
def test_create_regions(sut):
    regions = sut.create_regions()
    assert regions[1] == 'MockedRegion'
    assert regions[2] == 'MockedRegion'


@patch.object(DataInterface, '__init__', data_interface_init_mock)
@patch.object(Region, '__init__', region_init_mock)
def test_create_region(sut):
    region_id = 1
    region = sut._create_region(region_id)
    assert isinstance(region, Region)
