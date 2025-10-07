# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import patch

from data_interface import DataInterface


@pytest.fixture
def sut():
    scenario_options = {
        'id_product_filter': [],
        'co2_cost_2015_in_euro_per_ton_co2': 10,
        'co2_cost_2050_in_euro_per_ton_co2': 20,
    }

    with (
        patch('sqlite3.connect'),
        patch('pandas.read_sql_query'),
        patch('geopandas.points_from_xy'),
        patch('geopandas.GeoDataFrame'),
        patch('utils.collection_utils.join_with_comma'),
    ):
        return DataInterface(
            id_scenario=1,
            scenario_options=scenario_options,
            id_region=10,
        )


def test_co2_cost_in_euro_per_ton_co2(sut):
    with patch('utils.time_utils.interpolate', return_value='mocked_result') as patched_interpolate:
        result = sut.co2_cost_in_euro_per_ton_co2(year=2020)
        assert result == 'mocked_result'
        assert patched_interpolate.called


def test__read_energy_carrier_data(sut):
    with patch('pandas.read_sql_query') as patched_read_sql_query:
        sut._read_energy_carrier_data(connection='mocked_connection')
        assert patched_read_sql_query.called


def test__read_site_data(sut):
    with (
        patch('pandas.read_sql_query') as patched_read_sql_query,
        patch('geopandas.points_from_xy') as patched_points,
        patch('geopandas.GeoDataFrame') as patched_geo_data_frame,
    ):
        sut._read_site_data(connection='mocked_connection')
        assert patched_read_sql_query.called
        assert patched_points.called
        assert patched_geo_data_frame.called


def test__get_site_ids(sut):
    site_df = pd.DataFrame({'id': [10, 20], 'foo': [100, 200]})
    site_df = site_df.set_index(['id'])
    sut.site_data = site_df

    result = sut._get_site_ids()
    assert result == [10, 20]


class TestReadProductionUnitMappingAndDeleteUnusedSites:
    def test_without_product_filter(self, sut):
        df_mock = pd.DataFrame({'id_site': [1], 'id_product': [10]})

        with patch('utils.collection_utils.join_with_comma'), patch('pandas.read_sql_query', return_value=df_mock):
            result = sut._read_production_unit_mapping_and_delete_unused_sites(
                site_ids=[1],
                connection='mocked_connection',
                id_product_filter=[],
            )
            assert result[1].equals(df_mock)

    def test_with_product_filter(self, sut):
        with (
            patch('utils.collection_utils.join_with_comma'),
            patch('pandas.read_sql_query', return_value=pd.DataFrame()),
        ):
            result = sut._read_production_unit_mapping_and_delete_unused_sites(
                site_ids=[1],
                connection='mocked_connection',
                id_product_filter=[11],
            )
            assert len(result) == 0


class TestReadProductProcessMapping:
    def test__without_product_filter(self, sut):
        df_mock = pd.DataFrame({'id_product': [1], 'id_process': [10]})
        with patch('utils.collection_utils.join_with_comma'), patch('pandas.read_sql_query', return_value=df_mock):
            result = sut._read_product_process_mapping(connection='mocked_connection', id_product_filter=[])
            assert result[1].equals(df_mock)

    def test__with_product_filter(self, sut):
        with (
            patch('utils.collection_utils.join_with_comma'),
            patch('pandas.read_sql_query', return_value=pd.DataFrame()),
        ):
            result = sut._read_product_process_mapping(connection='mocked_connection', id_product_filter=[2])
            assert len(result) == 0


class TestReadProcessEnergyCarrierMapping:
    def test__without_product_filter(self, sut):
        df_mock = pd.DataFrame({'id_product': [1], 'id_process': [10], 'id_energy_carrier': [10], 'fuel_share': [0.5]})
        with patch('utils.collection_utils.join_with_comma'), patch('pandas.read_sql_query', return_value=df_mock):
            result = sut._read_process_energy_carrier_mapping(connection='mocked_connection', id_product_filter=[])
            assert result[1].equals(df_mock)

    def test__with_product_filter(self, sut):
        with (
            patch('utils.collection_utils.join_with_comma'),
            patch('pandas.read_sql_query', return_value=pd.DataFrame()),
        ):
            result = sut._read_process_energy_carrier_mapping(connection='mocked_connection', id_product_filter=[2])
            assert len(result) == 0


def test__read_energy_carrier_cost_mapping(sut):
    df_mock = pd.DataFrame({'id_product': [1], 'id_process': [10], 'id_energy_carrier': [10], 'fuel_share': [0.5]})
    with patch('utils.collection_utils.join_with_comma'), patch('pandas.read_sql_query', return_value=df_mock):
        result = sut._read_energy_carrier_cost_mapping('mocked_connection')
        assert result.equals(df_mock)


def test__read_energy_carrier_emission_mapping(sut):
    df_mock = pd.DataFrame({'id_product': [1], 'id_process': [10], 'id_energy_carrier': [10], 'fuel_share': [0.5]})
    with patch('utils.collection_utils.join_with_comma'), patch('pandas.read_sql_query', return_value=df_mock):
        result = sut._read_energy_carrier_emission_mapping('mocked_connection')
        assert result.equals(df_mock)
