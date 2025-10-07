# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import MagicMock, patch

from energy_carrier.energy_carrier_factory import EnergyCarrierFactory
from industrial_site.site_factory import SiteFactory
from region.region import Region


def energy_carrier_factory_init_mock(self, _data_interface):
    self.create_energy_carrier_map = MagicMock()


def site_factory_init_mock(self, _data_interface, _energy_carriers):
    self.create_sites = MagicMock()


@pytest.fixture
@patch.object(SiteFactory, '__init__', site_factory_init_mock)
@patch.object(EnergyCarrierFactory, '__init__', energy_carrier_factory_init_mock)
def sut():
    region = Region(id_region=1, data_interface=MagicMock())
    return region


def test_co2_cost_in_euro_per_ton_c02(sut):
    sut._data_interface.co2_cost_in_euro_per_ton_co2 = MagicMock(return_value='mocked_co2_cost')
    result = sut.co2_cost_in_euro_per_ton_c02(year=2020)
    assert result == 'mocked_co2_cost'


def test_process_year(sut):
    sut.co2_cost_in_euro_per_ton_c02 = MagicMock(return_value='mocked_co2_cost')
    site_mock = MagicMock()
    sut.sites = [site_mock]

    sut.process_year(
        year=2020,
        simulation_mode='mocked_simulation_mode',
        pipeline_cost_scaling=1,
        distance_to_closest_h2_pipeline=1,
    )

    assert sut.co2_cost_in_euro_per_ton_c02.called
    assert site_mock.process_year.called


def test_site_df(sut):
    sut._data_interface.site_data = pd.DataFrame(
        {
            'id_region': [1],
            'id_company': [10],
            'latitude': [5],
            'longitude': [50],
            'co2_equivalent_2015_in_tons': [100],
            'geometry': [None],
        },
    )
    result = sut.site_df()
    assert list(result.columns) == ['id_region', 'id_comp', 'latitude', 'longitude', 'co2_equ', 'geometry']


def test_accept(sut):
    site_mock = MagicMock()
    sut.sites = [site_mock]

    visitor = MagicMock()

    sut.accept(visitor, year=2020)

    assert visitor.visit_region.called
    assert site_mock.accept.called


def test_get_process_ids_for_site(sut):
    first_site_mock = MagicMock()
    first_site_mock.id = 1

    second_site_mock = MagicMock()
    second_site_mock.id = 2

    process_mock = MagicMock()
    process_mock.id = 'mocked_process_id'

    production_unit_mock = MagicMock()
    production_unit_mock.process = process_mock

    second_site_mock.production_units = [production_unit_mock]

    sut.sites = [first_site_mock, second_site_mock]

    result = sut.get_process_ids_for_site(id_site=2)

    assert result == ['mocked_process_id']
