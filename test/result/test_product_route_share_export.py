# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for product_route_share_export module."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

from result.product_route_share_export import (
    AMMONIA_PRODUCT_ID,
    METHANOL_PRODUCT_ID,
    OTHER_ROUTE,
    PRODUCT_ROUTE_DEFINITIONS,
    ROUTE_MIN_VALUE,
    _build_lhv_map,
    _build_product_rows,
    _classify_chain_into_routes,
    _filter_tables_for_region,
    _iamc_production_value,
    _iamc_variable_name,
    _merge_export_table,
    _purchase_route_bases,
    _region_ids_for_export,
    _region_name_map,
    _route_basis_for_chain,
    _TableContext,
)


class TestTableContext(unittest.TestCase):
    """Tests for _TableContext class."""

    def test_init_stores_tables(self):
        """Test that tables are stored."""
        tables_dict = {'table1': mock.MagicMock(), 'table2': mock.MagicMock()}
        context = _TableContext(tables_dict)
        assert context.tables == tables_dict

    def test_get_existing_table(self):
        """Test getting an existing table."""
        df = pd.DataFrame({'col': [1, 2, 3]})
        tables_dict = {'test': df}
        context = _TableContext(tables_dict)
        result = context.get('test')
        pd.testing.assert_frame_equal(result, df)

    def test_get_nonexistent_table(self):
        """Test getting a nonexistent table returns None."""
        context = _TableContext({})
        result = context.get('nonexistent')
        assert result is None

    def test_get_with_none_value(self):
        """Test getting a table with None value."""
        tables_dict = {'empty': None}
        context = _TableContext(tables_dict)
        result = context.get('empty')
        assert result is None


class TestRegionNameMap(unittest.TestCase):
    """Tests for _region_name_map function."""

    def test_region_name_map_empty_dataframe(self):
        """Test with empty dataframe."""
        df = pd.DataFrame({'id': [], 'name': []})
        result = _region_name_map(df)
        assert result == {}

    def test_region_name_map_none(self):
        """Test with None dataframe."""
        result = _region_name_map(None)
        assert result == {}

    def test_region_name_map_single_region(self):
        """Test with single region."""
        df = pd.DataFrame({'id': [1], 'name': ['Region A']})
        result = _region_name_map(df)
        assert result == {1: 'Region A'}

    def test_region_name_map_multiple_regions(self):
        """Test with multiple regions."""
        df = pd.DataFrame({'id': [1, 2, 3], 'name': ['North', 'South', 'West']})
        result = _region_name_map(df)
        assert result == {1: 'North', 2: 'South', 3: 'West'}

    def test_region_name_map_converts_to_int_and_str(self):
        """Test that id is converted to int and name to str."""
        df = pd.DataFrame({'id': ['1', '2'], 'name': [100, 200]})
        result = _region_name_map(df)
        assert result == {1: '100', 2: '200'}


class TestRegionIdsForExport(unittest.TestCase):
    """Tests for _region_ids_for_export function."""

    def test_region_ids_empty_dataframe(self):
        """Test with empty product dataframe."""
        tables = {'process_product_production_in_t': pd.DataFrame()}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == []

    def test_region_ids_missing_dataframe(self):
        """Test with missing product dataframe."""
        tables = {}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == []

    def test_region_ids_missing_id_region_column(self):
        """Test with missing id_region column."""
        df = pd.DataFrame({'id_product': [501], 'value': [100]})
        tables = {'process_product_production_in_t': df}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == []

    def test_region_ids_no_matching_products(self):
        """Test with no matching products."""
        df = pd.DataFrame({'id_product': [999], 'id_region': [1], 'id_scenario': [1]})
        tables = {'process_product_production_in_t': df}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == []

    def test_region_ids_single_region(self):
        """Test with single region."""
        df = pd.DataFrame({'id_product': [AMMONIA_PRODUCT_ID], 'id_region': [1], 'id_scenario': [1]})
        tables = {'process_product_production_in_t': df}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == [1]

    def test_region_ids_multiple_regions(self):
        """Test with multiple regions."""
        df = pd.DataFrame(
            {
                'id_product': [AMMONIA_PRODUCT_ID, METHANOL_PRODUCT_ID, AMMONIA_PRODUCT_ID],
                'id_region': [3, 1, 2],
                'id_scenario': [1, 1, 1],
            }
        )
        tables = {'process_product_production_in_t': df}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == [1, 2, 3]

    def test_region_ids_filters_by_scenario(self):
        """Test filtering by scenario ID."""
        df = pd.DataFrame({'id_product': [AMMONIA_PRODUCT_ID, AMMONIA_PRODUCT_ID], 'id_region': [1, 2], 'id_scenario': [1, 2]})
        tables = {'process_product_production_in_t': df}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == [1]

    def test_region_ids_ignores_nan_regions(self):
        """Test that NaN regions are ignored."""
        df = pd.DataFrame(
            {'id_product': [AMMONIA_PRODUCT_ID, AMMONIA_PRODUCT_ID], 'id_region': [1, pd.NA], 'id_scenario': [1, 1]}
        )
        tables = {'process_product_production_in_t': df}
        result = _region_ids_for_export(tables, scenario_id=1)
        assert result == [1]


class TestFilterTablesForRegion(unittest.TestCase):
    """Tests for _filter_tables_for_region function."""

    def test_filter_empty_tables(self):
        """Test filtering empty tables dict."""
        result = _filter_tables_for_region({}, region_id=1)
        assert result == {}

    def test_filter_preserves_region_table(self):
        """Test that region table is preserved."""
        region_df = pd.DataFrame({'id': [1, 2]})
        tables = {'id_region': region_df}
        result = _filter_tables_for_region(tables, region_id=1)
        pd.testing.assert_frame_equal(result['id_region'], region_df)

    def test_filter_preserves_lhv_table(self):
        """Test that LHV table is preserved."""
        lhv_df = pd.DataFrame({'Y2020': [1.0, 2.0]})
        tables = {'energy_carrier_lower_heating_value_in_gj_per_t': lhv_df}
        result = _filter_tables_for_region(tables, region_id=1)
        pd.testing.assert_frame_equal(result['energy_carrier_lower_heating_value_in_gj_per_t'], lhv_df)

    def test_filter_by_region_id(self):
        """Test filtering by region ID."""
        df = pd.DataFrame({'id_region': [1, 2, 1], 'value': [10, 20, 30]})
        tables = {'process_data': df}
        result = _filter_tables_for_region(tables, region_id=1)
        assert len(result['process_data']) == 2
        assert (result['process_data']['id_region'] == 1).all()

    def test_filter_by_scenario_and_region(self):
        """Test filtering by scenario and region."""
        df = pd.DataFrame({'id_scenario': [1, 1, 2], 'id_region': [1, 2, 1], 'value': [10, 20, 30]})
        tables = {'process_data': df}
        result = _filter_tables_for_region(tables, region_id=1, scenario_id=1)
        assert len(result['process_data']) == 1
        assert result['process_data'].iloc[0]['value'] == 10

    def test_filter_none_dataframe(self):
        """Test filtering None dataframe."""
        tables = {'data': None}
        result = _filter_tables_for_region(tables, region_id=1)
        assert result['data'] is None


class TestBuildLhvMap(unittest.TestCase):
    """Tests for _build_lhv_map function."""

    def test_build_lhv_map_none(self):
        """Test with None dataframe."""
        result = _build_lhv_map(None, 2020)
        assert result == {}

    def test_build_lhv_map_empty(self):
        """Test with empty dataframe."""
        df = pd.DataFrame()
        result = _build_lhv_map(df, 2020)
        assert result == {}

    def test_build_lhv_map_with_year_column(self):
        """Test with year column."""
        df = pd.DataFrame({'id_energy_carrier': [1, 2], 'Y2020': [25.0, 30.0]})
        result = _build_lhv_map(df, 2020)
        assert result == {1: 25.0, 2: 30.0}

    def test_build_lhv_map_with_alternative_column_names(self):
        """Test with alternative column names."""
        df = pd.DataFrame({'id': [1, 2], 'lower_heating_value_in_gj_per_t': [25.0, 30.0]})
        result = _build_lhv_map(df, 2020)
        assert result == {1: 25.0, 2: 30.0}

    def test_build_lhv_map_handles_nan(self):
        """Test that NaN values default to DEFAULT_LHV."""
        df = pd.DataFrame({'id_energy_carrier': [1, 2], 'Y2020': [25.0, None]})
        result = _build_lhv_map(df, 2020)
        assert result[1] == 25.0
        assert result[2] is not None

    def test_build_lhv_map_multiple_years(self):
        """Test with multiple year columns."""
        df = pd.DataFrame({'id_energy_carrier': [1, 2], 'Y2020': [25.0, 30.0], 'Y2021': [26.0, 31.0]})
        result_2020 = _build_lhv_map(df, 2020)
        result_2021 = _build_lhv_map(df, 2021)
        assert result_2020[1] == 25.0
        assert result_2021[1] == 26.0


class TestRouteBasisForChain(unittest.TestCase):
    """Tests for _route_basis_for_chain function."""

    def test_route_basis_no_data(self):
        """Test with empty chain."""
        mock_chain = mock.MagicMock()
        mock_chain.carrier_flows = []
        mock_chain.final_product_outputs = []
        mock_chain.product_flows = []
        mock_chain.by_product_flows = []

        result = _route_basis_for_chain(AMMONIA_PRODUCT_ID, mock_chain, {5120})
        assert result == 0.0

    def test_route_basis_from_carrier_for_ammonia(self):
        """Test carrier basis for ammonia."""
        mock_chain = mock.MagicMock()
        # (producer_id, carrier_id, consumer_id, amount)
        mock_chain.carrier_flows = [(5120, 2, 1, 100.0)]
        mock_chain.final_product_outputs = []
        mock_chain.product_flows = []
        mock_chain.by_product_flows = []

        result = _route_basis_for_chain(AMMONIA_PRODUCT_ID, mock_chain, {5120})
        assert result == 100.0

    def test_route_basis_from_final_output(self):
        """Test final output basis."""
        mock_chain = mock.MagicMock()
        mock_chain.carrier_flows = []
        # (producer_id, product_id, amount)
        mock_chain.final_product_outputs = [(5120, 501, 50.0)]
        mock_chain.product_flows = []
        mock_chain.by_product_flows = []

        result = _route_basis_for_chain(AMMONIA_PRODUCT_ID, mock_chain, {5120})
        assert result == 50.0

    def test_route_basis_from_product_flows(self):
        """Test product flow basis."""
        mock_chain = mock.MagicMock()
        mock_chain.carrier_flows = []
        mock_chain.final_product_outputs = []
        # (producer_id, product_id, consumer_id, amount)
        mock_chain.product_flows = [(5120, 501, 1, 25.0)]
        mock_chain.by_product_flows = []

        result = _route_basis_for_chain(AMMONIA_PRODUCT_ID, mock_chain, {5120})
        assert result == 25.0

    def test_route_basis_from_by_product(self):
        """Test by-product basis."""
        mock_chain = mock.MagicMock()
        mock_chain.carrier_flows = []
        mock_chain.final_product_outputs = []
        mock_chain.product_flows = []
        # (producer_id, by_product_id, consumer_id, amount)
        mock_chain.by_product_flows = [(5120, 100, 1, 10.0)]

        result = _route_basis_for_chain(AMMONIA_PRODUCT_ID, mock_chain, {5120})
        assert result == 10.0

    def test_route_basis_multiple_sources(self):
        """Test when multiple sources are available (carrier takes precedence)."""
        mock_chain = mock.MagicMock()
        mock_chain.carrier_flows = [(5120, 2, 1, 100.0)]
        mock_chain.final_product_outputs = [(5120, 501, 50.0)]
        mock_chain.product_flows = []
        mock_chain.by_product_flows = []

        result = _route_basis_for_chain(AMMONIA_PRODUCT_ID, mock_chain, {5120})
        # Carrier basis (100) takes precedence for ammonia
        assert result == 100.0


class TestPurchaseRouteBases(unittest.TestCase):
    """Tests for _purchase_route_bases function."""

    def test_purchase_route_bases_no_routes(self):
        """Test product without purchase routes."""
        mock_chain = mock.MagicMock()
        result = _purchase_route_bases(999, mock_chain)
        assert result == {}

    def test_purchase_route_bases_ammonia_imported_hydrogen(self):
        """Test ammonia imported hydrogen route."""
        mock_chain = mock.MagicMock()
        # (carrier_id, consumer_id, amount)
        mock_chain.purchased_carrier_flows = [(26, 1, 100.0)]
        mock_chain.purchased_product_flows = []

        result = _purchase_route_bases(AMMONIA_PRODUCT_ID, mock_chain)
        assert 'Imported hydrogen-derived' in result
        assert result['Imported hydrogen-derived'] == 100.0

    def test_purchase_route_bases_methanol_imported(self):
        """Test methanol imported route."""
        mock_chain = mock.MagicMock()
        mock_chain.purchased_carrier_flows = []
        # (product_id, consumer_id, amount)
        mock_chain.purchased_product_flows = [(METHANOL_PRODUCT_ID, 1, 75.0)]

        result = _purchase_route_bases(METHANOL_PRODUCT_ID, mock_chain)
        assert 'Imported methanol' in result
        assert result['Imported methanol'] == 75.0

    def test_purchase_route_bases_below_min_value(self):
        """Test that routes below minimum value are excluded."""
        mock_chain = mock.MagicMock()
        mock_chain.purchased_carrier_flows = [(26, 1, ROUTE_MIN_VALUE / 2)]
        mock_chain.purchased_product_flows = []

        result = _purchase_route_bases(AMMONIA_PRODUCT_ID, mock_chain)
        assert result == {}


class TestClassifyChainIntoRoutes(unittest.TestCase):
    """Tests for _classify_chain_into_routes function."""

    def test_classify_empty_chain(self):
        """Test with empty chain."""
        mock_chain = mock.MagicMock()
        mock_chain.final_product_outputs = []
        mock_chain.process_ids = set()
        mock_chain.carrier_flows = []
        mock_chain.product_flows = []
        mock_chain.by_product_flows = []
        mock_chain.purchased_carrier_flows = []
        mock_chain.purchased_product_flows = []

        result = _classify_chain_into_routes(AMMONIA_PRODUCT_ID, mock_chain)
        # All routes default to 0, plus OTHER_ROUTE
        assert OTHER_ROUTE in result
        assert result[OTHER_ROUTE] == 0.0

    def test_classify_single_route_matched(self):
        """Test with single matched route."""
        mock_chain = mock.MagicMock()
        mock_chain.final_product_outputs = [(5120, AMMONIA_PRODUCT_ID, 100.0)]
        mock_chain.process_ids = {5120}
        mock_chain.carrier_flows = [(5120, 2, 1, 50.0)]
        mock_chain.product_flows = []
        mock_chain.by_product_flows = []
        mock_chain.purchased_carrier_flows = []
        mock_chain.purchased_product_flows = []

        result = _classify_chain_into_routes(AMMONIA_PRODUCT_ID, mock_chain)
        assert result['SMR'] == 100.0
        assert result[OTHER_ROUTE] == 0.0

    def test_classify_multiple_routes(self):
        """Test with multiple matched routes."""
        mock_chain = mock.MagicMock()
        mock_chain.final_product_outputs = [(5120, AMMONIA_PRODUCT_ID, 50.0), (5130, AMMONIA_PRODUCT_ID, 50.0)]
        mock_chain.process_ids = {5120, 5130}
        mock_chain.carrier_flows = [(5120, 2, 1, 25.0), (5130, 2, 1, 25.0)]
        mock_chain.product_flows = []
        mock_chain.by_product_flows = []
        mock_chain.purchased_carrier_flows = []
        mock_chain.purchased_product_flows = []

        result = _classify_chain_into_routes(AMMONIA_PRODUCT_ID, mock_chain)
        assert result['SMR'] == 50.0
        assert result['SMR + CCS'] == 50.0


class TestBuildProductRows(unittest.TestCase):
    """Tests for _build_product_rows function."""

    def test_build_product_rows_empty(self):
        """Test with empty production."""
        with mock.patch(
            'result.product_route_share_export._calculate_route_production_for_region_and_year',
            return_value=dict.fromkeys(PRODUCT_ROUTE_DEFINITIONS[AMMONIA_PRODUCT_ID], 0.0),
        ):
            rows = _build_product_rows('Test Region', 'Test Scenario', AMMONIA_PRODUCT_ID, [2020], {}, 'production_in_t')
        assert len(rows) > 0

    def test_build_product_rows_production_values(self):
        """Test production value rows."""
        production = {'SMR': 100.0, OTHER_ROUTE: 50.0}
        with mock.patch(
            'result.product_route_share_export._calculate_route_production_for_region_and_year', return_value=production
        ):
            rows = _build_product_rows('Test Region', 'Test Scenario', AMMONIA_PRODUCT_ID, [2020], {}, 'production_in_t')

        smr_row = next((r for r in rows if r['route'] == 'SMR'), None)
        assert smr_row is not None
        assert smr_row['production_in_t'] == 100.0

    def test_build_product_rows_share_values(self):
        """Test share percentage rows."""
        production = {'SMR': 100.0, OTHER_ROUTE: 50.0}
        with mock.patch(
            'result.product_route_share_export._calculate_route_production_for_region_and_year', return_value=production
        ):
            rows = _build_product_rows('Test Region', 'Test Scenario', AMMONIA_PRODUCT_ID, [2020], {}, 'share_in_percent')

        smr_row = next((r for r in rows if r['route'] == 'SMR'), None)
        assert smr_row is not None
        # 100 / (100 + 50) * 100 = 66.67%
        assert smr_row['share_in_percent'] == pytest.approx(66.67, abs=0.05)

    def test_build_product_rows_contains_required_fields(self):
        """Test that rows contain all required fields."""
        production = {'SMR': 100.0}
        with mock.patch(
            'result.product_route_share_export._calculate_route_production_for_region_and_year', return_value=production
        ):
            rows = _build_product_rows('Test Region', 'Test Scenario', AMMONIA_PRODUCT_ID, [2020], {}, 'production_in_t')

        if rows:
            row = rows[0]
            assert 'scenario' in row
            assert 'region' in row
            assert 'product' in row
            assert 'route' in row
            assert 'year' in row


class TestIamcVariableName(unittest.TestCase):
    """Tests for _iamc_variable_name function."""

    def test_iamc_variable_name(self):
        """Test IAMC variable name generation."""
        row = {'product': 'Ammonia', 'route': 'SMR'}
        result = _iamc_variable_name(row)
        assert result == 'Ammonia|SMR'

    def test_iamc_variable_name_with_spaces(self):
        """Test IAMC variable name with spaces."""
        row = {'product': 'Ammonia', 'route': 'SMR + CCS'}
        result = _iamc_variable_name(row)
        assert result == 'Ammonia|SMR + CCS'


class TestIamcProductionValue(unittest.TestCase):
    """Tests for _iamc_production_value function."""

    def test_iamc_production_value_single_ton(self):
        """Test converting tons to Mt/year."""
        row = {'production_in_t': 1_000_000.0}  # 1 Mt in tons
        unit, value = _iamc_production_value(row)
        assert unit == 'Mt/year'
        assert value == 1.0

    def test_iamc_production_value_multiple_tons(self):
        """Test converting multiple tons."""
        row = {'production_in_t': 5_000_000.0}  # 5 Mt in tons
        unit, value = _iamc_production_value(row)
        assert unit == 'Mt/year'
        assert value == 5.0

    def test_iamc_production_value_small_amount(self):
        """Test small production amounts."""
        row = {'production_in_t': 500_000.0}  # 0.5 Mt
        _unit, value = _iamc_production_value(row)
        assert value == 0.5


class TestMergeExportTable(unittest.TestCase):
    """Tests for _merge_export_table function."""

    def test_merge_new_to_empty_database(self):
        """Test merging new data to empty database."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / 'test.db'
            new_df = pd.DataFrame({'region': ['A'], 'product': ['Ammonia'], 'Y2020': [100.0]})

            conn = sqlite3.connect(db_path)
            try:
                result = _merge_export_table(conn, 'test_table', new_df, ['region', 'product'])
            finally:
                conn.close()

            pd.testing.assert_frame_equal(result, new_df)
        finally:
            import shutil

            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_merge_preserves_existing_data(self):
        """Test that merge preserves existing data."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / 'test.db'

            existing_df = pd.DataFrame({'region': ['A', 'B'], 'product': ['Ammonia', 'Ammonia'], 'Y2020': [100.0, 200.0]})

            new_df = pd.DataFrame({'region': ['C'], 'product': ['Ammonia'], 'Y2020': [300.0]})

            # Create table with existing data
            conn = sqlite3.connect(db_path)
            try:
                existing_df.to_sql('test_table', conn, if_exists='replace', index=False)
                conn.commit()
            finally:
                conn.close()

            # Merge new data
            conn = sqlite3.connect(db_path)
            try:
                result = _merge_export_table(conn, 'test_table', new_df, ['region', 'product'])
            finally:
                conn.close()

            assert len(result) == 3
        finally:
            import shutil

            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_merge_overwrites_matching_rows(self):
        """Test that matching rows are overwritten."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / 'test.db'

            existing_df = pd.DataFrame({'region': ['A'], 'product': ['Ammonia'], 'Y2020': [100.0]})

            new_df = pd.DataFrame({'region': ['A'], 'product': ['Ammonia'], 'Y2020': [150.0]})

            # Create table with existing data
            conn = sqlite3.connect(db_path)
            try:
                existing_df.to_sql('test_table', conn, if_exists='replace', index=False)
                conn.commit()
            finally:
                conn.close()

            # Merge new data
            conn = sqlite3.connect(db_path)
            try:
                result = _merge_export_table(conn, 'test_table', new_df, ['region', 'product'])
            finally:
                conn.close()

            # Should have 1 row with new value
            assert len(result) == 1
            assert result.iloc[0]['Y2020'] == 150.0
        finally:
            import shutil

            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
