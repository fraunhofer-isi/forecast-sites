# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import MagicMock, patch

from visitor.tabular_result_visitor import TabularResultVisitor


@pytest.fixture
def sut():
    return TabularResultVisitor()


def test_visit_region(sut):
    region_mock = MagicMock()
    sut.visit_region(region_mock, year=2020)
    assert sut._region == region_mock


def test_visit_site(sut):
    site_mock = MagicMock()
    site_mock.id = 'mocked_id'
    sut.visit_site(site_mock, year=2020)
    assert sut._id_site == 'mocked_id'


def test_production_unit(sut):
    production_unit_mock = MagicMock()
    production_unit_mock.id = 'mocked_id'
    sut.visit_production_unit(production_unit_mock, year=2020)
    assert sut._id_production_unit == 'mocked_id'


def test_visit_product(sut):
    product_mock = MagicMock()
    product_mock.id = 'mocked_id'
    sut.visit_product(product_mock, year=2020)
    assert sut._id_product == 'mocked_id'


def test_visit_process(sut):
    sut._region = MagicMock()
    sut._add_entry = MagicMock()
    sut._add_energy_carrier_entry = MagicMock()

    energy_demand_mock = MagicMock()

    process_mock = MagicMock()
    process_mock.id = 'mocked_id'
    process_mock.energy_demands = [energy_demand_mock]
    sut.visit_process(process_mock, year=2020)
    assert sut._id_process == 'mocked_id'


def test_finalize(sut):
    sut._save = MagicMock()
    with patch('utils.file_utils.create_folder_if_not_exists') as patched_create_folder:
        sut.finalize()

        assert patched_create_folder.called
        assert sut._save.called


def test__save(sut):
    create_empty_table = TabularResultVisitor._create_empty_table_for_df
    TabularResultVisitor._create_empty_table_for_df = MagicMock()

    df = pd.DataFrame({'foo': [1]})
    df.to_sql = MagicMock()
    df.to_excel = MagicMock()

    with patch('sqlite3.connect'):
        with patch('utils.file_utils.delete_file_if_exists') as patched_delete_file:
            sut._save(df, 'mocked_name', 'mocked_output_folder')

            assert patched_delete_file.called
            assert TabularResultVisitor._create_empty_table_for_df.called
            assert df.to_sql.called
            assert df.to_excel.called

    TabularResultVisitor._create_empty_table_for_df = create_empty_table


def test__create_empty_table_for_df():
    df = pd.DataFrame({'foo': [1], 'baa': [10]})
    df = df.set_index(['foo'])

    mocked_connection = MagicMock()
    mocked_connection.execute = MagicMock()

    TabularResultVisitor._create_empty_table_for_df(df, 'mocked_name', mocked_connection)

    assert mocked_connection.execute.called


def test__add_entry(sut):
    sut._base_row = MagicMock()
    sut._add_entry_at = MagicMock()

    sut._add_entry('df_mock', year=2020, value=1000)

    assert sut._base_row.called
    assert sut._add_entry_at.called


def test__add_energy_carrier_entry(sut):
    sut._base_row = MagicMock()
    sut._add_entry_at = MagicMock()

    sut._add_energy_carrier_entry('df_mock', id_energy_carrier=1, year=2020, value=1000)

    assert sut._base_row.called
    assert sut._add_entry_at.called


class TestAddEntryAt:

    def test_existing_index(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10]})
        df = df.set_index(['id_region', 'id_site'])
        keys = tuple(1, 10)

        sut._add_entry_at(df, keys, year=2020, value=1000)

        assert list(df.columns) == ['Y2020']

        row = df.loc[keys]
        assert row['Y2020'] == 1000

    def test_not_existing_index(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10]})
        df = df.set_index(['id_region', 'id_site'])
        keys = tuple(2, 20)
        sut._add_entry_at(df, keys, year=2020, value=1000)

        assert list(df.columns) == ['Y2020']

        row = df.loc[keys]
        assert row['Y2020'] == 1000


def test__initialize_production_df(sut):
    result = sut._initialize_production_df()
    assert result.index.names == sut._base_column_names


def test__initialize_emission_df(sut):
    result = sut._initialize_process_emission_df()
    assert result.index.names == sut._base_column_names


def test__initialize_final_energy_demand_df(sut):
    result = sut._initialize_final_energy_demand_df()
    assert result.index.names == [*sut._base_column_names, 'id_energy_carrier']


def test__initialize_production_cost_df(sut):
    result = sut._initialize_production_cost_df()
    assert result.index.names == [*sut._base_column_names, 'id_energy_carrier']


def test_initialize_production_cost_per_ton_df(sut):
    result = sut._initialize_production_cost_per_ton_df()
    assert result.index.names == sut._base_column_names


def test__initialize_energy_cost_df(sut):
    result = sut._initialize_energy_cost_df()
    assert result.index.names == [*sut._base_column_names, 'id_energy_carrier']


def test__base_row(sut):
    sut._region = MagicMock()
    sut._region.id = 1
    sut._id_site = 10
    sut._id_production_unit = 100
    sut._id_product = 1000
    sut._id_process = 10000
    result = sut._base_row()
    assert result == [1, 10, 100, 1000, 10000]
