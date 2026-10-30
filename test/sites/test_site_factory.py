# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import geopandas
import pandas as pd
import pytest
from shapely.geometry import Point
from test_utils.isi_mock import Mock, patch

from processes.process_factory import ProcessFactory
from production_unit.production_unit_factory import ProductionUnitFactory
from sites.site import Site
from sites.site_factory import SiteFactory
from sub_production_unit.sub_production_unit_factory import SubProductionUnitFactory


@pytest.fixture
@patch(SiteFactory._merge_carriers, [])
@patch(ProcessFactory.__init__, None)
@patch(SubProductionUnitFactory.__init__, None)
@patch(ProductionUnitFactory.__init__, None)
def sut():
    data_interface = Mock()
    site_data_df = pd.DataFrame(
        [
            {
                'id': 1,
                'id_region': 10,
                'id_company': 100,
                'latitude': 50,
                'longitude': 60,
                'co2_equivalent_start_year_in_t': 1000,
                'geometry': Point(6, 49),
            }
        ],
    ).set_index('id')

    site_data = geopandas.GeoDataFrame(site_data_df, geometry='geometry')

    data_interface.site_data = site_data
    sector_map = {}
    process_map = {}
    energy_carriers = {}
    product_map = {}
    by_product_map = {}

    optimization_factory = Mock()

    simulation_options = {
        'start_year': 2000,
        'end_year': 2050,
    }
    site_factory = SiteFactory(
        data_interface,
        sector_map,
        process_map,
        energy_carriers,
        product_map,
        by_product_map,
        optimization_factory,
        simulation_options,
    )
    site_factory._production_unit_factory = Mock(return_value=None)
    return site_factory


def test_construction(sut):
    assert sut is not None


def test_merge_carriers(sut):
    energy_carrier_dictionary = {'a': 'b'}
    products_dictionary = {'c': 'd'}
    by_products_dictionary = {'e': 'f'}

    carriers = sut._merge_carriers(
        energy_carrier_dictionary,
        products_dictionary,
        by_products_dictionary,
    )
    assert carriers == ['b', 'd', 'f']


@pytest.mark.filterwarnings('ignore:The array interface.*')
class TestCreateSites:
    @staticmethod
    def mocked_create_site(
        _row,
        _region,
    ):
        return 'mocked_site'

    # @patch(SiteFactory._create_site, site_init_mock)
    def test_with_site_data(self, sut):
        sut._create_site = TestCreateSites.mocked_create_site
        sites = sut.create_sites('mocked_region')

        assert len(sites) == 1
        assert sites[0] == 'mocked_site'

    def test_without_site_data(self, sut):
        sut._site_data = []
        mocked_region = Mock()
        mocked_region.id = 'mocked_id_region'
        with pytest.raises(ValueError, match='No sites found'):
            sut.create_sites(mocked_region)


@patch(Site.__init__, None)
def test_create_site(sut):
    row = Mock()
    row.name = 39
    row['geometry'] = Point(6, 49)

    result = sut._create_site(row, 'mocked_region')
    assert isinstance(result, Site)
