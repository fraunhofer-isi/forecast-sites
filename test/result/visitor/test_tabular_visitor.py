# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import logging
import sqlite3

import pandas as pd
import pytest
from test_utils.isi_mock import Mock, fixture, patch

from result.visitor.tabular_visitor import TabularVisitor
from utils import data_frame_utils, file_utils, time_utils


@fixture
@patch(TabularVisitor._initialize)
def sut():
    return TabularVisitor('mocked_simulation_options')


def test_construction(sut):
    assert sut is not None


def test_initialize(sut):
    sut._initialize()
    assert True


def test_finalize(sut):
    sut._simulation_options = {'output_directory': 'mocked_output_folder'}
    with (
        patch(TabularVisitor._finalize_results) as patched_finalize_results,
        patch(file_utils.create_folder_if_not_exists) as patched_create_folder,
    ):
        sut.finalize()
        assert patched_create_folder.called
        assert patched_finalize_results.called


def test_save(sut):
    create_empty_table = TabularVisitor._create_empty_table
    TabularVisitor._create_empty_table = Mock()

    df = pd.DataFrame({'foo': [1]})
    df.to_sql = Mock()
    df.to_excel = Mock()

    with (
        patch(sqlite3.connect),
        patch(file_utils.delete_file_if_exists) as patched_delete_file,
    ):
        sut._save(df, 'mocked_name', 'mocked_output_folder')

        assert patched_delete_file.called
        assert TabularVisitor._create_empty_table.called
        assert df.to_sql.called
        assert df.to_excel.called

    TabularVisitor._create_empty_table = create_empty_table


class TestSave:
    @patch(TabularVisitor._merge_with_existing)
    @patch(TabularVisitor._save_as_sqlite_table)
    @patch(TabularVisitor._save_as_excel_file)
    def test_with_empty_dataframe(self, sut):
        df = pd.DataFrame()

        with patch(logging.info) as mocked_info:
            sut._save(df, 'mocked_name', 'mocked_output_folder')
            assert mocked_info.called

    @patch(TabularVisitor._save_as_excel_file)
    def test_normal_usage(self, sut):
        df = pd.DataFrame({'foo': [1]})
        with (
            patch(TabularVisitor._merge_with_existing, side_effect=lambda current_df, _name, _folder: current_df),
            patch(TabularVisitor._save_as_sqlite_table) as mocked_save_as_sqlite_table,
        ):
            sut._save(df, 'mocked_name', 'mocked_output_folder')
            assert mocked_save_as_sqlite_table.called


@patch(TabularVisitor._create_empty_table)
def test_save_as_sqlite_table(sut):
    df = pd.DataFrame({'foo': [1]})
    df.to_sql = Mock()
    with patch(sqlite3.connect):
        sut._save_as_sqlite_table(df, 'mocked_name', 'mocked_output_folder')
        assert df.to_sql.called


@patch(TabularVisitor._create_empty_table)
def test_save_as_sqlite_table_with_empty_dataframe(sut):
    """Test _save_as_sqlite_table with empty dataframe (to_sql should not be called)."""
    df = pd.DataFrame({'foo': []})
    df.to_sql = Mock()
    with patch(sqlite3.connect):
        sut._save_as_sqlite_table(df, 'mocked_name', 'mocked_output_folder')
        # to_sql should NOT be called when df is empty (line 95: if not df.empty)
        assert not df.to_sql.called


@patch(file_utils.delete_file_if_exists)
def test_save_as_excel_file(sut):  # keep backwards compatibility with original patch
    df = pd.DataFrame({'foo': [1]})
    df.to_excel = Mock()
    with patch(sqlite3.connect):
        sut._save_as_excel_file(df, 'mocked_name', 'mocked_output_folder')
        assert df.to_excel.called


def test_merge_results_keeps_rows_for_multiple_scenarios():
    existing_df = pd.DataFrame(
        {'Y2025': [100.0]},
        index=pd.MultiIndex.from_tuples([(1, 18)], names=['id_scenario', 'id_region']),
    )
    new_df = pd.DataFrame(
        {'Y2025': [200.0]},
        index=pd.MultiIndex.from_tuples([(2, 18)], names=['id_scenario', 'id_region']),
    )

    merged_df = TabularVisitor._merge_results(existing_df, new_df)

    assert merged_df.loc[(1, 18), 'Y2025'] == 100.0
    assert merged_df.loc[(2, 18), 'Y2025'] == 200.0


def test_merge_results_returns_new_when_existing_empty():
    """Test _merge_results when existing_df is empty."""
    existing_df = pd.DataFrame({'Y2025': []})
    new_df = pd.DataFrame({'Y2025': [100.0]})

    merged_df = TabularVisitor._merge_results(existing_df, new_df)

    assert merged_df.equals(new_df)


def test_merge_results_returns_existing_when_new_empty():
    """Test _merge_results when new_df is empty."""
    existing_df = pd.DataFrame({'Y2025': [100.0]})
    new_df = pd.DataFrame({'Y2025': []})

    merged_df = TabularVisitor._merge_results(existing_df, new_df)

    assert merged_df.equals(existing_df)


def test_read_existing_table_returns_empty_for_missing_table():
    connection = sqlite3.connect(':memory:')
    reference_df = pd.DataFrame(columns=['id_scenario', 'id_region']).set_index(['id_scenario', 'id_region'])

    result = TabularVisitor._read_existing_table(connection, 'missing_table', reference_df)

    assert result.empty
    assert result.index.names == ['id_scenario', 'id_region']
    connection.close()


def test_read_existing_table_sets_index_when_names_present():
    """Test that _read_existing_table sets index when reference_df has index names."""
    connection = sqlite3.connect(':memory:')

    # Create a table with data
    existing_df = pd.DataFrame({'id_scenario': [1], 'id_region': [10], 'Y2025': [100.0]})
    existing_df.to_sql('test_table', connection, index=False)

    # Create reference_df with index names
    reference_df = pd.DataFrame(columns=['id_scenario', 'id_region', 'Y2025']).set_index(['id_scenario', 'id_region'])

    result = TabularVisitor._read_existing_table(connection, 'test_table', reference_df)

    # Should have set the index to match reference_df
    assert result.index.names == ['id_scenario', 'id_region']
    assert result.loc[(1, 10), 'Y2025'] == 100.0
    connection.close()


def test_read_existing_table_no_index_when_names_absent():
    """Test that _read_existing_table skips set_index when reference_df has no index names."""
    connection = sqlite3.connect(':memory:')

    # Create a table with data
    existing_df = pd.DataFrame({'col1': [1], 'col2': [10], 'Y2025': [100.0]})
    existing_df.to_sql('test_table', connection, index=False)

    # Create reference_df WITHOUT index names (plain dataframe, no set_index)
    reference_df = pd.DataFrame(columns=['col1', 'col2', 'Y2025'])

    result = TabularVisitor._read_existing_table(connection, 'test_table', reference_df)

    # Should NOT have set index (stays as default RangeIndex)
    assert result.index.names == [None]  # Default index has no names
    assert result.loc[0, 'Y2025'] == 100.0
    connection.close()


def test_merge_with_existing_returns_df_on_operational_error():
    """Test that _merge_with_existing returns df when sqlite3.OperationalError occurs."""
    df = pd.DataFrame({'Y2025': [100.0]})

    # Create a path that will cause OperationalError (non-existent directory)
    output_folder = '/nonexistent/path/that/does/not/exist'

    # Since we can't actually create that path without error, mock the sqlite3.connect to raise
    with patch(sqlite3.connect, side_effect=sqlite3.OperationalError('Cannot open database')):
        result = TabularVisitor._merge_with_existing(df, 'test_table', output_folder)

    # Should return the original df when error occurs
    assert result.equals(df)


def test_create_empty_table():
    df = pd.DataFrame({'foo': [1], 'baa': [10]})
    df = df.set_index(['foo'])

    mocked_connection = Mock()
    mocked_connection.execute = Mock()

    TabularVisitor._create_empty_table(df, 'mocked_name', mocked_connection)

    assert mocked_connection.execute.called


class TestAddEntryAt:
    def test_existing_index(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10]})
        df = df.set_index(['id_region', 'id_site'])
        keys = (1, 10)

        sut._add_entry_at(df, keys, 2020, 1000)

        assert list(df.columns) == ['Y2020']

        row = df.loc[keys]
        assert row['Y2020'] == 1000

    def test_not_existing_index(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10]})
        df = df.set_index(['id_region', 'id_site'])
        keys = (2, 20)
        sut._add_entry_at(df, keys, 2020, 1000)

        assert list(df.columns) == ['Y2020']

        row = df.loc[keys]
        assert row['Y2020'] == 1000

    def test_already_existing_entry(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10], 'Y2020': [500]})
        df = df.set_index(['id_region', 'id_site'])
        keys = (1, 10)

        with pytest.raises(KeyError, match='Entry for keys'):
            sut._add_entry_at(df, keys, 2020, 1000)


class TestAddOrAccumulateEntryAt:
    def test_existing_index_without_entry(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10]})
        df = df.set_index(['id_region', 'id_site'])
        keys = (1, 10)

        sut._add_or_accumulate_entry_at(df, keys, 2020, 1000)

        assert list(df.columns) == ['Y2020']

        row = df.loc[keys]
        assert row['Y2020'] == 1000

    def test_existing_index_with_entry(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10], 'Y2020': [500]})
        df = df.set_index(['id_region', 'id_site'])
        keys = (1, 10)

        sut._add_or_accumulate_entry_at(df, keys, 2020, 1000)

        assert list(df.columns) == ['Y2020']

        row = df.loc[keys]
        assert row['Y2020'] == 1500

    def test_not_existing_index(self, sut):
        df = pd.DataFrame({'id_region': [1], 'id_site': [10]})
        df = df.set_index(['id_region', 'id_site'])
        keys = (2, 20)
        sut._add_or_accumulate_entry_at(df, keys, 2020, 1000)

        assert list(df.columns) == ['Y2020']

        row = df.loc[keys]
        assert row['Y2020'] == 1000


def test_site_row(sut):
    sut._id_scenario = 1
    sut._region = Mock()
    sut._region.id = 2
    sut._id_site = 3
    result = sut._site_row()
    assert result == [1, 2, 3]


def test_production_unit_row(sut):
    sut._id_scenario = 1
    sut._region = Mock()
    sut._region.id = 2
    sut._id_site = 3
    sut._id_production_unit = 4
    result = sut._production_unit_row()
    assert result == [1, 2, 3, 4]


def test_base_row(sut):
    sut._id_scenario = 1
    sut._region = Mock()
    sut._region.id = 2
    sut._id_site = 3
    sut._id_production_unit = 4
    sut._id_sub_production_unit = 5
    sut._id_process = 6
    result = sut._base_row()
    assert result == [1, 2, 3, 4, 5, 6]


def test_empty_region_energy_carrier_table(sut):
    result = sut._empty_region_energy_carrier_table()
    assert result.index.names == ['id_scenario', 'id_region', 'id_energy_carrier']


def test_empty_region_table(sut):
    result = sut._empty_region_table()
    assert result.index.names == ['id_scenario', 'id_region']


def test_empty_sector_energy_carrier_table(sut):
    result = sut._empty_sector_energy_carrier_table()
    assert result.index.names == ['id_scenario', 'id_region', 'id_sector', 'id_energy_carrier']


def test_empty_sector_table(sut):
    result = sut._empty_sector_table()
    assert result.index.names == ['id_scenario', 'id_region', 'id_sector']


def test_empty_site_table(sut):
    result = sut._empty_site_table()
    assert result.index.names == sut._site_indices


def test_empty_site_energy_carrier_table(sut):
    result = sut._empty_site_energy_carrier_table()
    assert result.index.names == [*sut._site_indices, 'id_energy_carrier']


def test_empty_site_product_table(sut):
    result = sut._empty_site_product_table()
    assert result.index.names == [*sut._site_indices, 'id_product']


def test_empty_site_by_product_table(sut):
    result = sut._empty_site_by_product_table()
    assert result.index.names == [*sut._site_indices, 'id_by_product']


def test_empty_production_unit_table(sut):
    result = sut._empty_production_unit_table()
    assert result.index.names == sut._production_unit_indices


def test_empty_production_unit_energy_carrier_table(sut):
    result = sut._empty_production_unit_energy_carrier_table()
    assert result.index.names == [*sut._production_unit_indices, 'id_energy_carrier']


def test_empty_production_unit_product_table(sut):
    result = sut._empty_production_unit_product_table()
    assert result.index.names == [*sut._production_unit_indices, 'id_product']


def test_empty_production_unit_by_product_table(sut):
    result = sut._empty_production_unit_by_product_table()
    assert result.index.names == [*sut._production_unit_indices, 'id_by_product']


def test_empty_base_table(sut):
    result = sut._empty_base_table()
    assert result.index.names == sut._base_indices


def test_empty_energy_carrier_table(sut):
    result = sut._empty_energy_carrier_table()
    assert result.index.names == [*sut._base_indices, 'id_energy_carrier']


def test_empty_product_table(sut):
    result = sut._empty_product_table()
    assert result.index.names == [*sut._base_indices, 'id_product']


def test_empty_by_product_table(sut):
    result = sut._empty_by_product_table()
    assert result.index.names == [*sut._base_indices, 'id_by_product']


def test_add_region_energy_carrier_entry_or_accumulate(sut):
    with patch(TabularVisitor._add_or_accumulate_entry_at) as mocked_add_or_accumulate_entry_at:
        sut._add_region_energy_carrier_entry_or_accumulate('df_mock', 7, 2020, 1000)
        assert mocked_add_or_accumulate_entry_at.called


def test_add_sector_energy_carrier_entry_or_accumulate(sut):
    with patch(TabularVisitor._add_or_accumulate_entry_at) as mocked_add_or_accumulate_entry_at:
        sut._add_sector_energy_carrier_entry_or_accumulate('df_mock', 7, 2020, 1000)
        assert mocked_add_or_accumulate_entry_at.called


def test_add_sector_energy_carrier_entry(sut):
    with patch(TabularVisitor._add_entry_at) as mocked_add_entry_at:
        sut._add_sector_energy_carrier_entry('df_mock', 7, 2020, 2020, 1000)
        assert mocked_add_entry_at.called


def test_add_region_entry_or_accumulate(sut):
    with patch(TabularVisitor._add_or_accumulate_entry_at) as mocked_add_or_accumulate_entry_at:
        sut._add_region_entry_or_accumulate('df_mock', 2020, 1000)
        assert mocked_add_or_accumulate_entry_at.called


def test_add_sector_entry_or_accumulate(sut):
    with patch(TabularVisitor._add_or_accumulate_entry_at) as mocked_add_or_accumulate_entry_at:
        sut._add_sector_entry_or_accumulate('df_mock', 2020, 1000)
        assert mocked_add_or_accumulate_entry_at.called


def test_add_site_entry(sut):
    sut._site_row = Mock(return_value=[1, 2, 3])
    sut._add_entry_at = Mock()
    sut._add_site_entry('df_mock', 2020, 1000)
    assert sut._site_row.called
    assert sut._add_entry_at.called


def test_add_site_energy_carrier_entry(sut):
    sut._site_row = Mock(return_value=[1, 2, 3])
    sut._add_entry_at = Mock()
    sut._add_site_energy_carrier_entry('df_mock', 7, 2020, 1000)
    assert sut._site_row.called
    assert sut._add_entry_at.called


def test_add_site_product_entry(sut):
    sut._site_row = Mock(return_value=[1, 2, 3])
    sut._add_entry_at = Mock()
    sut._add_site_product_entry('df_mock', 8, 2020, 1000)
    assert sut._site_row.called
    assert sut._add_entry_at.called


def test_add_site_by_product_entry(sut):
    sut._site_row = Mock(return_value=[1, 2, 3])
    sut._add_entry_at = Mock()
    sut._add_site_by_product_entry('df_mock', 9, 2020, 1000)
    assert sut._site_row.called
    assert sut._add_entry_at.called


def test_add_production_unit_entry(sut):
    sut._production_unit_row = Mock(return_value=[1, 2, 3, 4])
    sut._add_entry_at = Mock()
    sut._add_production_unit_entry('df_mock', 2020, 1000)
    assert sut._production_unit_row.called
    assert sut._add_entry_at.called


def test_add_production_unit_energy_carrier_entry(sut):
    sut._production_unit_row = Mock(return_value=[1, 2, 3, 4])
    sut._add_entry_at = Mock()
    sut._add_production_unit_energy_carrier_entry('df_mock', 7, 2020, 1000)
    assert sut._production_unit_row.called
    assert sut._add_entry_at.called


def test_add_production_unit_product_entry(sut):
    sut._production_unit_row = Mock(return_value=[1, 2, 3, 4])
    sut._add_entry_at = Mock()
    sut._add_production_unit_product_entry('df_mock', 8, 2020, 1000)
    assert sut._production_unit_row.called
    assert sut._add_entry_at.called


def test_add_production_unit_by_product_entry(sut):
    sut._production_unit_row = Mock(return_value=[1, 2, 3, 4])
    sut._add_entry_at = Mock()
    sut._add_production_unit_by_product_entry('df_mock', 9, 2020, 1000)
    assert sut._production_unit_row.called
    assert sut._add_entry_at.called


def test_add_entry(sut):
    sut._base_row = Mock()
    sut._add_entry_at = Mock()
    sut._add_entry('df_mock', 2020, 1000)
    assert sut._base_row.called
    assert sut._add_entry_at.called


def test_add_energy_carrier_entry(sut):
    sut._base_row = Mock()
    sut._add_entry_at = Mock()
    sut._add_energy_carrier_entry('df_mock', 1, 2020, 1000)
    assert sut._base_row.called
    assert sut._add_entry_at.called


def test_add_product_entry(sut):
    sut._base_row = Mock()
    sut._add_entry_at = Mock()
    sut._add_product_entry('df_mock', 1, 2020, 1000)
    assert sut._base_row.called
    assert sut._add_entry_at.called


def test_add_by_product_entry(sut):
    sut._base_row = Mock()
    sut._add_entry_at = Mock()
    sut._add_by_product_entry('df_mock', 1, 2020, 1000)
    assert sut._base_row.called
    assert sut._add_entry_at.called


@patch(time_utils.create_time_span)
@patch(data_frame_utils.ensure_year_columns_exist)
def test_finalize_results(sut):
    sut._simulation_options = {
        'start_year': 2020,
        'end_year': 2025,
        'year_increment': 1,
    }

    sut._absolute_results = {'foo': 'mocked_df'}
    sut._specific_results = {'foo': 'mocked_df'}
    with patch(TabularVisitor._save) as mocked_save:
        sut._finalize_results('mocked_output_folder')
        assert mocked_save.called
