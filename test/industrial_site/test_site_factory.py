# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import geopandas
import pandas as pd
import pytest
from mock import MagicMock, Mock, patch
from shapely.geometry import Point

from industrial_site.site import Site
from industrial_site.site_factory import SiteFactory


@pytest.fixture
def sut():
    data_interface = MagicMock()
    site_data_df = pd.DataFrame(
        {
            'id': [1],
            'id_region': [10],
            'id_company': [100],
            'latitude': [50],
            'longitude': [60],
            'co2_equivalent_2015_in_tons': [1000],
            'geometry': [Point(6, 49)],
        },
    )
    site_data_df.set_index('id')
    site_data = geopandas.GeoDataFrame(site_data_df, geometry='geometry')

    data_interface.site_data = site_data

    energy_carriers = MagicMock()
    site_factory = SiteFactory(data_interface, energy_carriers)
    site_factory._production_unit_factory = Mock(return_value=None)
    return site_factory


def site_init_mock(
    self,
    id_site,
    _geometry,
    _production_units,
):
    self.id = id_site


@pytest.mark.filterwarnings('ignore:The array interface.*')
class TestCreateSites:
    def test_with_data(self, sut):
        sut._create_site = Mock(return_value='dummy_site')
        sites = sut.create_sites()
        assert len(sites) == 1
        assert sites[0] == 'dummy_site'

    def test_without_data(self, sut):
        sut._site_data = []
        sut._create_site = Mock(return_value='dummy_site')
        sites = sut.create_sites()
        assert len(sites) == 0


@patch.object(Site, '__init__', site_init_mock)
@pytest.mark.filterwarnings('ignore:The array interface.*')
def test_create_site(sut):
    row = MagicMock()
    row.name = 39
    row['geometry'] = Point(6, 49)

    site = sut._create_site(row)
    assert site.id == 39
