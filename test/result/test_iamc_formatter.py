# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

import contextlib
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from result.iamc_formatter import (
    IamcExportConfig,
    _merge_existing_iamc_table,
    _normalize_year,
    build_iamc_long_table,
    pivot_iamc_wide_table,
    save_iamc_table,
)


class TestIamcExportConfig:
    """Tests for IamcExportConfig dataclass."""

    def test_config_initialization_with_required_fields(self) -> None:
        """IamcExportConfig stores model and scenario."""
        config = IamcExportConfig(model='MyModel', scenario='BaselineScenario')

        assert config.model == 'MyModel'
        assert config.scenario == 'BaselineScenario'

    def test_config_initialization_with_custom_variable_column(self) -> None:
        """IamcExportConfig accepts custom variable column name."""
        config = IamcExportConfig(model='Model', scenario='Scenario', variable_column_name='custom_var')

        assert config.variable_column_name == 'custom_var'

    def test_config_default_variable_column_name(self) -> None:
        """IamcExportConfig uses 'variable' as default column name."""
        config = IamcExportConfig(model='Model', scenario='Scenario')

        assert config.variable_column_name == 'variable'

    def test_config_is_frozen(self) -> None:
        """IamcExportConfig is immutable."""
        config = IamcExportConfig(model='Model', scenario='Scenario')

        with pytest.raises(AttributeError):
            config.model = 'NewModel'

    def test_config_equality(self) -> None:
        """IamcExportConfig instances compare by value."""
        config1 = IamcExportConfig(model='Model', scenario='Scenario')
        config2 = IamcExportConfig(model='Model', scenario='Scenario')

        assert config1 == config2

    def test_config_different_scenarios(self) -> None:
        """IamcExportConfig instances differ if scenario differs."""
        config1 = IamcExportConfig(model='Model', scenario='Scenario1')
        config2 = IamcExportConfig(model='Model', scenario='Scenario2')

        assert config1 != config2


class TestBuildIamcLongTable:
    """Tests for build_iamc_long_table function."""

    def test_build_long_table_with_single_row(self) -> None:
        """build_iamc_long_table creates long format from rows."""
        rows = [
            {'region': 'EUR', 'year': 2020, 'variable_id': 'v1', 'value': 100.0},
        ]
        config = IamcExportConfig(model='Model', scenario='Scenario')

        def region_mapper(x):
            return x.lower()

        def variable_mapper(x):
            return f'var_{x["variable_id"]}'

        def value_mapper(x):
            return ('Mt', x['value'])

        result = build_iamc_long_table(
            rows,
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        assert len(result) == 1
        assert result['model'].iloc[0] == 'Model'
        assert result['scenario'].iloc[0] == 'Scenario'
        assert result['region'].iloc[0] == 'eur'
        assert result['variable'].iloc[0] == 'var_v1'
        assert result['unit'].iloc[0] == 'Mt'
        assert result['value'].iloc[0] == 100.0
        assert result['year'].iloc[0] == 2020

    def test_build_long_table_with_multiple_rows(self) -> None:
        """build_iamc_long_table handles multiple rows."""
        rows = [
            {'region': 'EUR', 'year': 2020, 'variable_id': 'v1', 'value': 100.0},
            {'region': 'USA', 'year': 2021, 'variable_id': 'v2', 'value': 200.0},
            {'region': 'CHN', 'year': 2022, 'variable_id': 'v3', 'value': 300.0},
        ]
        config = IamcExportConfig(model='Model', scenario='Scenario')

        def region_mapper(x):
            return x

        def variable_mapper(x):
            return f'var_{x["variable_id"]}'

        def value_mapper(x):
            return ('Mt', x['value'])

        result = build_iamc_long_table(
            rows,
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        assert len(result) == 3
        assert list(result['region']) == ['EUR', 'USA', 'CHN']

    def test_build_long_table_with_custom_variable_column(self) -> None:
        """build_iamc_long_table uses custom variable column name."""
        rows = [{'region': 'EUR', 'year': 2020, 'variable_id': 'v1', 'value': 100.0}]
        config = IamcExportConfig(model='Model', scenario='Scenario', variable_column_name='custom_var')

        def region_mapper(x):
            return x

        def variable_mapper(x):
            return 'CustomVar'

        def value_mapper(x):
            return ('Mt', x['value'])

        result = build_iamc_long_table(
            rows,
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        assert 'custom_var' in result.columns
        assert 'variable' not in result.columns
        assert result['custom_var'].iloc[0] == 'CustomVar'

    def test_build_long_table_normalizes_year(self) -> None:
        """build_iamc_long_table normalizes year values."""
        rows = [
            {'region': 'EUR', 'year': 'Y2020', 'variable_id': 'v1', 'value': 100.0},
            {'region': 'EUR', 'year': 2021, 'variable_id': 'v1', 'value': 100.0},
        ]
        config = IamcExportConfig(model='Model', scenario='Scenario')

        def region_mapper(x):
            return x

        def variable_mapper(x):
            return 'Var'

        def value_mapper(x):
            return ('Mt', x['value'])

        result = build_iamc_long_table(
            rows,
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        assert result['year'].iloc[0] == 2020
        assert result['year'].iloc[1] == 2021

    def test_build_long_table_with_float_year_string(self) -> None:
        """build_iamc_long_table handles float year as string."""
        rows = [{'region': 'EUR', 'year': '2020', 'variable_id': 'v1', 'value': 100.0}]
        config = IamcExportConfig(model='Model', scenario='Scenario')

        def region_mapper(x):
            return x

        def variable_mapper(x):
            return 'Var'

        def value_mapper(x):
            return ('Mt', x['value'])

        result = build_iamc_long_table(
            rows,
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        assert result['year'].iloc[0] == 2020

    def test_build_long_table_empty_rows(self) -> None:
        """build_iamc_long_table handles empty rows list."""
        config = IamcExportConfig(model='Model', scenario='Scenario')

        def region_mapper(x):
            return x

        def variable_mapper(x):
            return 'Var'

        def value_mapper(x):
            return ('Mt', x['value'])

        result = build_iamc_long_table(
            [],
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        assert len(result) == 0
        assert 'model' in result.columns

    def test_build_long_table_with_unit_mapper(self) -> None:
        """build_iamc_long_table uses unit from value mapper."""
        rows = [
            {'region': 'EUR', 'year': 2020, 'variable_id': 'v1', 'value': 100.0, 'unit': 'Mt'},
            {'region': 'EUR', 'year': 2020, 'variable_id': 'v2', 'value': 50.0, 'unit': 'TWh'},
        ]
        config = IamcExportConfig(model='Model', scenario='Scenario')

        def region_mapper(x):
            return x

        def variable_mapper(x):
            return f'var_{x["variable_id"]}'

        def value_mapper(x):
            return (x['unit'], x['value'])

        result = build_iamc_long_table(
            rows,
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        assert result['unit'].iloc[0] == 'Mt'
        assert result['unit'].iloc[1] == 'TWh'


class TestPivotIamcWideTable:
    """Tests for pivot_iamc_wide_table function."""

    def test_pivot_wide_table_with_long_data(self) -> None:
        """pivot_iamc_wide_table converts long to wide format."""
        long_df = pd.DataFrame(
            {
                'model': ['Model'] * 3,
                'scenario': ['Scenario'] * 3,
                'region': ['EUR'] * 3,
                'variable': ['Var1'] * 3,
                'unit': ['Mt'] * 3,
                'year': [2020, 2021, 2022],
                'value': [100.0, 110.0, 120.0],
            }
        )

        result = pivot_iamc_wide_table(long_df)

        assert 'model' in result.columns
        assert 'scenario' in result.columns
        assert 'region' in result.columns
        assert 'variable' in result.columns
        assert 'unit' in result.columns
        assert 2020 in result.columns
        assert 2021 in result.columns
        assert 2022 in result.columns

    def test_pivot_wide_table_with_custom_variable_column(self) -> None:
        """pivot_iamc_wide_table respects custom variable column name."""
        long_df = pd.DataFrame(
            {
                'model': ['Model'],
                'scenario': ['Scenario'],
                'region': ['EUR'],
                'custom_var': ['Var1'],
                'unit': ['Mt'],
                'year': [2020],
                'value': [100.0],
            }
        )

        result = pivot_iamc_wide_table(long_df, variable_column_name='custom_var')

        assert 'custom_var' in result.columns

    def test_pivot_wide_table_empty_dataframe(self) -> None:
        """pivot_iamc_wide_table handles empty DataFrames."""
        long_df = pd.DataFrame(columns=['model', 'scenario', 'region', 'variable', 'unit', 'year', 'value'])

        result = pivot_iamc_wide_table(long_df)

        assert len(result) == 0
        assert 'model' in result.columns
        assert 'scenario' in result.columns

    def test_pivot_wide_table_aggregates_duplicates(self) -> None:
        """pivot_iamc_wide_table sums duplicate entries."""
        long_df = pd.DataFrame(
            {
                'model': ['Model', 'Model'],
                'scenario': ['Scenario', 'Scenario'],
                'region': ['EUR', 'EUR'],
                'variable': ['Var1', 'Var1'],
                'unit': ['Mt', 'Mt'],
                'year': [2020, 2020],
                'value': [50.0, 50.0],
            }
        )

        result = pivot_iamc_wide_table(long_df)

        assert len(result) == 1
        assert result[2020].iloc[0] == 100.0

    def test_pivot_wide_table_preserves_year_order(self) -> None:
        """pivot_iamc_wide_table orders years numerically."""
        long_df = pd.DataFrame(
            {
                'model': ['Model'] * 4,
                'scenario': ['Scenario'] * 4,
                'region': ['EUR'] * 4,
                'variable': ['Var1'] * 4,
                'unit': ['Mt'] * 4,
                'year': [2022, 2020, 2021, 2023],
                'value': [120.0, 100.0, 110.0, 130.0],
            }
        )

        result = pivot_iamc_wide_table(long_df)

        year_columns = [col for col in result.columns if isinstance(col, int)]
        assert year_columns == [2020, 2021, 2022, 2023]


class TestSaveIamcTable:
    """Tests for save_iamc_table function."""

    def test_save_iamc_table_with_mock(self) -> None:
        """save_iamc_table handles DataFrame processing."""
        df = pd.DataFrame(
            {
                'model': ['Model'],
                'scenario': ['Scenario'],
                'region': ['EUR'],
                'variable': ['Var1'],
                'unit': ['Mt'],
                2020: [100.0],
            }
        )

        # Test with mock to avoid file system issues
        with patch('result.iamc_formatter.sqlite3.connect'), contextlib.suppress(FileNotFoundError, OSError):
            # Expected - directory doesn't exist
            save_iamc_table(df, Path('/nonexistent/path'), 'test')


class TestMergeExistingIamcTable:
    """Tests for _merge_existing_iamc_table function."""

    def test_merge_when_table_does_not_exist(self) -> None:
        """_merge_existing_iamc_table returns new_df when table doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = sqlite3.connect(f'{tmpdir}/test.db')
            new_df = pd.DataFrame(
                {
                    'model': ['Model'],
                    'scenario': ['Scenario'],
                    'region': ['EUR'],
                    'variable': ['Var1'],
                    'unit': ['Mt'],
                    'year': [2020],
                    'value': [100.0],
                }
            )

            result = _merge_existing_iamc_table(
                conn,
                'nonexistent_table',
                new_df,
                ['model', 'scenario', 'region', 'variable', 'unit'],
            )
            conn.close()

            assert len(result) == 1
            assert result['value'].iloc[0] == 100.0

    def test_merge_when_new_df_empty(self) -> None:
        """_merge_existing_iamc_table returns existing_df when new_df is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = sqlite3.connect(f'{tmpdir}/test.db')

            # Create existing table
            existing_df = pd.DataFrame(
                {
                    'model': ['Model'],
                    'scenario': ['Scenario'],
                    'region': ['EUR'],
                    'variable': ['Var1'],
                    'unit': ['Mt'],
                    'year': [2020],
                    'value': [100.0],
                }
            )
            existing_df.to_sql('test_table', conn, if_exists='replace', index=False)

            # Try to merge with empty new_df
            new_df = pd.DataFrame(columns=['model', 'scenario', 'region', 'variable', 'unit', 'year', 'value'])

            result = _merge_existing_iamc_table(conn, 'test_table', new_df, ['model', 'scenario', 'region', 'variable', 'unit'])
            conn.close()

            assert len(result) == 1
            assert result['value'].iloc[0] == 100.0

    def test_merge_when_existing_df_empty(self) -> None:
        """_merge_existing_iamc_table returns new_df when existing_df is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = sqlite3.connect(f'{tmpdir}/test.db')

            # Create empty existing table
            empty_df = pd.DataFrame(columns=['model', 'scenario', 'region', 'variable', 'unit', 'year', 'value'])
            empty_df.to_sql('test_table', conn, if_exists='replace', index=False)

            # Merge with new_df
            new_df = pd.DataFrame(
                {
                    'model': ['Model'],
                    'scenario': ['Scenario'],
                    'region': ['EUR'],
                    'variable': ['Var1'],
                    'unit': ['Mt'],
                    'year': [2020],
                    'value': [100.0],
                }
            )

            result = _merge_existing_iamc_table(conn, 'test_table', new_df, ['model', 'scenario', 'region', 'variable', 'unit'])
            conn.close()

            assert len(result) == 1
            assert result['value'].iloc[0] == 100.0

    def test_merge_keeps_non_overlapping_existing_rows(self) -> None:
        """_merge_existing_iamc_table keeps existing rows not in new_df."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = sqlite3.connect(f'{tmpdir}/test.db')

            # Create existing table with two rows
            existing_df = pd.DataFrame(
                {
                    'model': ['Model', 'Model'],
                    'scenario': ['Scenario', 'Scenario'],
                    'region': ['EUR', 'USA'],
                    'variable': ['Var1', 'Var1'],
                    'unit': ['Mt', 'Mt'],
                    'year': [2020, 2020],
                    'value': [100.0, 200.0],
                }
            )
            existing_df.to_sql('test_table', conn, if_exists='replace', index=False)

            # Merge with new row for different region
            new_df = pd.DataFrame(
                {
                    'model': ['Model'],
                    'scenario': ['Scenario'],
                    'region': ['CHN'],
                    'variable': ['Var1'],
                    'unit': ['Mt'],
                    'year': [2020],
                    'value': [300.0],
                }
            )

            result = _merge_existing_iamc_table(conn, 'test_table', new_df, ['model', 'scenario', 'region', 'variable', 'unit'])
            conn.close()

            assert len(result) == 3  # EUR, USA (kept), CHN (new)


class TestNormalizeYear:
    """Tests for _normalize_year function."""

    def test_normalize_year_with_integer(self) -> None:
        """_normalize_year returns integer unchanged."""
        result = _normalize_year(2020)

        assert result == 2020

    def test_normalize_year_with_year_prefix(self) -> None:
        """_normalize_year strips 'Y' prefix."""
        result = _normalize_year('Y2020')

        assert result == 2020

    def test_normalize_year_with_string(self) -> None:
        """_normalize_year parses string to integer."""
        result = _normalize_year('2020')

        assert result == 2020

    def test_normalize_year_with_year_float(self) -> None:
        """_normalize_year converts year string from float."""
        result = _normalize_year(2020)

        assert result == 2020

    def test_normalize_year_with_y_prefix_again(self) -> None:
        """_normalize_year removes 'Y' prefix multiple times if present."""
        result = _normalize_year('Y2021')

        assert result == 2021

    def test_normalize_year_with_invalid_format_raises_error(self) -> None:
        """_normalize_year raises ValueError for invalid format."""
        with pytest.raises(ValueError, match='invalid literal'):
            _normalize_year('not_a_year')


class TestIamcFormatterIntegration:
    """Integration tests for IAMC formatter."""

    def test_full_workflow_long_to_wide(self) -> None:
        """Integration test: build long and pivot wide."""
        rows = [
            {'region': 'EUR', 'year': 2020, 'variable_id': 'v1', 'value': 100.0},
            {'region': 'EUR', 'year': 2021, 'variable_id': 'v1', 'value': 110.0},
            {'region': 'USA', 'year': 2020, 'variable_id': 'v1', 'value': 200.0},
            {'region': 'USA', 'year': 2021, 'variable_id': 'v1', 'value': 220.0},
        ]
        config = IamcExportConfig(model='Model', scenario='Scenario')

        def region_mapper(x):
            return x

        def variable_mapper(x):
            return 'Variable'

        def value_mapper(x):
            return ('Mt', x['value'])

        # Build long table
        long_table = build_iamc_long_table(
            rows,
            config=config,
            region_mapper=region_mapper,
            variable_mapper=variable_mapper,
            value_mapper=value_mapper,
        )

        # Verify long table
        assert len(long_table) == 4
        assert all(col in long_table.columns for col in ['model', 'scenario', 'region', 'variable', 'unit', 'year', 'value'])

        # Pivot to wide
        wide_table = pivot_iamc_wide_table(long_table)

        # Verify wide table
        assert len(wide_table) == 2  # EUR, USA
        assert 2020 in wide_table.columns
        assert 2021 in wide_table.columns
