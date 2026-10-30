# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import sqlite3

import pandas as pd
import pytest
from test_utils.isi_mock import (
    Mock,
    fixture,
    original_patch,
    patch,
    patch_property,
    patch_sqlite_connect,
)

from data_layer.data_interface import DataInterface
from utils import collection_utils


# noinspection PyProtectedMember
@fixture
@patch(DataInterface._read_tables_from_database)
def sut():
    simulation_options = {
        'id_product_filter': [],
        'database_path': 'mocked_path',
    }
    return DataInterface(
        1,
        10,
        simulation_options,
    )


def test_construction(sut):
    assert sut is not None


def test_end_year(sut):
    sut._simulation_options = {
        'end_year': 2020,
    }
    result = sut._end_year
    assert result == 2020


class TestInterestRate:
    def test_zero_value(self, sut):
        sut._interest_rate_data = pd.DataFrame([{'interest_rate': 0}])
        with pytest.raises(ValueError, match='needs to be'):
            _interest_rate = sut.interest_rate

    def test_normal_usage(self, sut):
        sut._interest_rate_data = pd.DataFrame([{'interest_rate': 0.05}])
        result = sut.interest_rate
        assert result == 0.05


def test_co2_cost_in_euro_per_t_co2(sut):
    sut._co2_cost = pd.DataFrame([{'2020': 11.0, '2030': 22.0}])

    # Requesting year 2020 falls between 2019 and 2021, so it returns the last available year's value (2021)
    result = sut.co2_cost_in_euro_per_t_co2(2020)
    assert result == 11.0


def test_co2_cost_in_euro_per_t_co2_falls_back_to_last_available_year(sut):
    sut._co2_cost = pd.DataFrame([{'2020': 11.0, '2030': 22.0}])

    result = sut.co2_cost_in_euro_per_t_co2(2040)

    assert result == 22.0


class TestEnergyCarrierAvailabilitySeries:
    def test_without_entry(self, sut):
        sut._energy_carrier_availability = pd.DataFrame(
            [
                {'id_energy_carrier': 1},
            ]
        ).set_index('id_energy_carrier')
        mocked_carrier = Mock()
        mocked_carrier.id = 2

        result = sut.energy_carrier_availability_series(mocked_carrier)
        assert result is None

    def test_with_entry(self, sut):
        sut._energy_carrier_availability = pd.DataFrame(
            [
                {'id_energy_carrier': 1, '2015': 11, '2016': 22},
            ]
        ).set_index('id_energy_carrier')
        mocked_carrier = Mock()
        mocked_carrier.id = 1

        result = sut.energy_carrier_availability_series(mocked_carrier)
        assert result['2015'] == 11


class TestProductAvailabilitySeries:
    def test_without_entry(self, sut):
        sut._product_availability = pd.DataFrame(
            [
                {'id_product': 1},
            ]
        ).set_index('id_product')
        mocked_product = Mock()
        mocked_product.id = 2

        result = sut.product_availability_series(mocked_product)
        assert result is None

    def test_with_entry(self, sut):
        sut._product_availability = pd.DataFrame(
            [
                {'id_product': 1, '2015': 11, '2016': 22},
            ]
        ).set_index('id_product')
        mocked_product = Mock()
        mocked_product.id = 1

        result = sut.product_availability_series(mocked_product)
        assert result['2015'] == 11


class TestByProductAvailabilitySeries:
    def test_without_entry(self, sut):
        sut._by_product_availability = pd.DataFrame(
            [
                {'id_by_product': 1},
            ]
        ).set_index('id_by_product')
        mocked_by_product = Mock()
        mocked_by_product.id = 2

        result = sut.by_product_availability_series(mocked_by_product)
        assert result is None

    def test_with_entry(self, sut):
        sut._by_product_availability = pd.DataFrame(
            [
                {'id_by_product': 1, '2015': 11, '2016': 22},
            ]
        ).set_index('id_by_product')
        mocked_by_product = Mock()
        mocked_by_product.id = 1

        result = sut.by_product_availability_series(mocked_by_product)
        assert result['2015'] == 11


@patch_property(DataInterface._end_year, 2050)
def test_annual_value_series(sut):
    result = sut.annual_value_series(100, 2015)
    assert len(result) == 2050 - 2015 + 1
    assert result['2015'] == 100
    assert result['2050'] == 100


def test_read_region_tables(sut):
    with patch(DataInterface._filtered_scenario_table) as mocked_filtered_table:
        sut._read_region_tables('mocked_connection')
        assert mocked_filtered_table.called


@patch(DataInterface.database_connection, patch_sqlite_connect())
@patch(DataInterface._read_region_tables)
@patch(DataInterface._read_site_tables)
@patch(DataInterface._read_production_unit_tables)
@patch(DataInterface._read_process_tables)
@patch(DataInterface._read_energy_carrier_tables)
@patch(DataInterface._read_product_tables)
@patch(DataInterface._read_by_product_tables)
@patch(DataInterface._read_sector_tables)
def test_read_tables_from_database_and_create_class_attributes(sut):
    sut._read_tables_from_database('mocked_id_product_filter')


@patch(DataInterface._site_data)
@patch(DataInterface._site_ids)
@patch(
    DataInterface._read_production_units_by_sites,
    ('mocked_site_production_unit_mapping', 'mocked_result'),
)
def test_read_site_tables(sut):
    result = sut._read_site_tables('mocked_connection', 'mocked_id_product_filter')
    assert result == 'mocked_result'


@patch(DataInterface._read_production_unit_sub_production_unit_mapping)
@patch(DataInterface._read_production_unit_product_mapping)
def test_read_production_unit_tables(sut):
    sut._read_production_unit_tables(
        'mocked_connection',
        'mocked_id_product_filter',
        'mocked_production_unit_ids',
    )


@patch(DataInterface.id_table)
def test_read_sector_tables(sut):
    sut._read_sector_tables('mocked_connection')


@patch(DataInterface.table)
def test_read_process_tables(sut):
    sut._read_process_tables('mocked_connection')


@patch(DataInterface.id_table)
@patch(DataInterface._filtered_scenario_table)
@patch(DataInterface.table, Mock('mocked_table'))
def test_read_energy_carrier_tables(sut):
    sut._read_energy_carrier_tables('mocked_connection')


@patch(DataInterface.id_table)
@patch(DataInterface._filtered_scenario_table)
@patch(DataInterface.table, Mock('mocked_table'))
def test_read_product_tables(sut):
    sut._read_product_tables('mocked_connection')


@patch(DataInterface.id_table)
@patch(DataInterface._filtered_scenario_table)
@patch(DataInterface.table, Mock('mocked_table'))
def test_read_by_product_tables(sut):
    sut._read_by_product_tables('mocked_connection')


class TestDatabaseConnection:
    def test_without_error(self, sut):
        with patch(sqlite3.connect, patch_sqlite_connect()):
            result = sut.database_connection('mocked_path')
            assert result is not None

    @patch(sqlite3.connect, Mock(side_effect=sqlite3.Error))
    def test_with_error(self, sut):
        with pytest.raises(OSError, match='Could not find input'):
            sut.database_connection('mocked_path')


@original_patch('pandas.read_sql_query', Mock('mocked_result'))
def test_id_table(sut):
    result = sut.id_table('mocked_connection', 'mocked_table_name')
    assert result == 'mocked_result'


@patch(DataInterface._id_column_names)
@original_patch('pandas.read_sql_query', Mock())
def test_table(sut):
    result = sut.table('mocked_connection', 'mocked_table_name')
    assert result is not None


@original_patch('pandas.read_sql_query', Mock())
def test_id_column_names(sut):
    result = sut._id_column_names('mocked_connection', 'mocked_table_name')
    assert result is not None


@patch(collection_utils.join_with_comma)
@original_patch('pandas.read_sql_query', Mock('mocked_result'))
def test_read_production_units(sut):
    result = sut._read_production_units('mocked_connection', 'mocked_production_unit_id_filter')
    assert result == 'mocked_result'


@patch(collection_utils.join_with_comma)
@original_patch('pandas.read_sql_query', Mock())
def test_read_production_unit_sub_production_unit_mapping(sut):
    result = sut._read_production_unit_sub_production_unit_mapping('mocked_connection', 'mocked_production_unit_id_filter')
    assert result is not None


@patch(collection_utils.join_with_comma)
def test_read_production_units_by_site(sut):
    df_mock = pd.DataFrame(
        [
            {'id': 1, 'id_site': 1, 'id_product': 10},
        ]
    ).set_index('id')

    with original_patch('pandas.read_sql_query', return_value=df_mock):
        site_map, all_production_unit_ids = sut._read_production_units_by_sites('mocked_connection', [1])
        assert site_map[1].equals(df_mock)

        assert all_production_unit_ids == [1]


@patch(collection_utils.join_with_comma)
class TestReadProductProductionUnitMapping:
    def test_without_product_filter(self, sut):
        df_mock = pd.DataFrame({'id_product': [1]})
        with original_patch('pandas.read_sql_query', return_value=df_mock):
            result = sut._read_production_unit_product_mapping('mocked_connection', [])
            assert result.equals(df_mock)

    class TestWithProductFilter:
        def test_with_empty_data_frame(self, sut):
            with (
                original_patch('pandas.read_sql_query', return_value=pd.DataFrame()),
                pytest.raises(ValueError, match='No production units found'),
            ):
                sut._read_production_unit_product_mapping('mocked_connection', [2])

        def test_with_non_empty_data_frame(self, sut):
            df_mock = pd.DataFrame({'id_product': [1]})
            with original_patch('pandas.read_sql_query', return_value=df_mock):
                result = sut._read_production_unit_product_mapping('mocked_connection', [2])
                assert len(result) == 1


def test_geo_data_frame(sut):
    df = pd.DataFrame([{'id': 1, 'longitude': 10, 'latitude': 20}]).set_index('id')
    result = sut._geo_data_frame(df)

    assert result.crs == 'EPSG:4326'

    point = result.loc[1]['geometry']
    assert point.x == 10
    assert point.y == 20


@patch(DataInterface.table)
@patch(DataInterface._filter_for_scenario_and_region, 'mocked_result')
def test_filtered_scenario_table(sut):
    result = sut._filtered_scenario_table('mocked_connection', 'mocked_table_name')
    assert result == 'mocked_result'


class TestFilterForScenarioAndRegion:
    def test_empty_table(self, sut):
        mocked_df = Mock()
        mocked_df.query = Mock(pd.DataFrame())
        with pytest.raises(KeyError):
            sut._filter_for_scenario_and_region(mocked_df, 'mocked_table')

    def test_non_empty_table(self, sut):
        sut.id_scenario = 3
        sut.id_region = 6
        df_mock = pd.DataFrame(
            [
                {'id_scenario': 3, 'id_region': 6, 'id_foo': 33, 'value': 44},
            ]
        ).set_index(['id_scenario', 'id_region', 'id_foo'])
        mocked_df = Mock()
        mocked_df.query = Mock(df_mock)

        result = sut._filter_for_scenario_and_region(mocked_df, 'mocked_table')
        assert result.loc[33]['value'] == 44


@patch(DataInterface._potential_site_ids)
@patch(DataInterface._geo_data_frame, 'mocked_result')
@original_patch(
    'pandas.read_sql_query',
    Mock(pd.DataFrame([{'id_site': 1, 'latitude': 20, 'longitude': 10}]).set_index('id_site')),
)
def test_site_data(sut):
    mocked_df = Mock()
    mocked_df.empty = False
    mocked_df.join = Mock(return_value='mocked_result')
    with original_patch('pandas.read_sql_query', return_value=mocked_df):
        result = sut._site_data('mocked_connection', 'mocked_id_product_filter')
        assert result == 'mocked_result'


@patch(DataInterface._potential_site_ids)
@original_patch('pandas.read_sql_query', Mock(pd.DataFrame()))
def test_site_data_raises_when_no_sites_match_region_and_product_filter(sut):
    with pytest.raises(ValueError, match='No sites with production units found'):
        sut._site_data('mocked_connection', 'mocked_id_product_filter')


@patch(DataInterface._read_production_unit_product_mapping)
class TestProductionUnits:
    @patch(DataInterface._read_production_units, ['mocked_production_unit'])
    def test_with_production_units(self, sut):
        result = sut._production_units('mocked_connection', 'mocked_id_product_filter')
        assert result == ['mocked_production_unit']

    @patch(DataInterface._read_production_units, [])
    def test_without_production_units(self, sut):
        with pytest.raises(ValueError, match='No production units found'):
            sut._production_units('mocked_connection', 'mocked_id_product_filter')


@patch(DataInterface._production_units)
@patch(collection_utils.join_with_comma, 'mocked_result')
def test_potential_site_ids(sut):
    result = sut._potential_site_ids('mocked_connection', 'mocked_id_product_filter')
    assert result == 'mocked_result'


def test_site_ids(sut):
    site_df = pd.DataFrame({'id': [10, 20], 'foo': [100, 200]})
    site_df = site_df.set_index(['id'])
    sut.site_data = site_df

    result = sut._site_ids()
    assert result == [10, 20]


@patch(DataInterface.database_connection, patch_sqlite_connect())
@original_patch(
    'pandas.read_sql_query', Mock(pd.DataFrame([{'id_group': 1, 'branch': 2, 'id_region': 10, 'description': 'foo'}]))
)
def test_groups_for_region(sut):
    result = sut.groups_for_region(10)

    assert result == [{'id_group': 1, 'branch': 2, 'id_region': 10, 'description': 'foo'}]


@patch(DataInterface.database_connection, patch_sqlite_connect())
@original_patch('pandas.read_sql_query', Mock(pd.DataFrame([{'id_group': 1, 'id_site': 5}])))
def test_group_site_memberships(sut):
    result = sut.group_site_memberships(10)

    assert result == [{'id_group': 1, 'id_site': 5}]
