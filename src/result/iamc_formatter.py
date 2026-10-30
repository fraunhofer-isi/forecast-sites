# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path

IamcRegionMapper = Callable[[str], str]
IamcVariableMapper = Callable[[dict], str]
IamcValueMapper = Callable[[dict], tuple[str, float]]


@dataclass(frozen=True)
class IamcExportConfig:
    model: str
    scenario: str
    variable_column_name: str = 'variable'


def build_iamc_long_table(
    rows: list[dict],
    *,
    config: IamcExportConfig,
    region_mapper: IamcRegionMapper,
    variable_mapper: IamcVariableMapper,
    value_mapper: IamcValueMapper,
) -> pd.DataFrame:
    iamc_rows = []
    for row in rows:
        unit, value = value_mapper(row)
        iamc_rows.append(
            {
                'model': config.model,
                'scenario': config.scenario,
                'region': region_mapper(str(row['region'])),
                config.variable_column_name: variable_mapper(row),
                'unit': unit,
                'year': _normalize_year(row['year']),
                'value': float(value),
            }
        )

    columns = ['model', 'scenario', 'region', config.variable_column_name, 'unit', 'year', 'value']
    return pd.DataFrame(iamc_rows, columns=columns)


def pivot_iamc_wide_table(df: pd.DataFrame, *, variable_column_name: str = 'variable') -> pd.DataFrame:
    index_columns = ['model', 'scenario', 'region', variable_column_name, 'unit']
    if df.empty:
        return pd.DataFrame(columns=index_columns)

    wide_df = df.pivot_table(index=index_columns, columns='year', values='value', aggfunc='sum').reset_index()
    wide_df.columns.name = None
    year_columns = sorted(column for column in wide_df.columns if isinstance(column, int))
    return wide_df[index_columns + year_columns]


def save_iamc_table(df: pd.DataFrame, output_directory: Path, table_name: str) -> None:
    sqlite_path = output_directory / 'output.sqlite'
    index_columns = ['model', 'scenario', 'region', 'variable', 'unit']
    connection = sqlite3.connect(sqlite_path)
    try:
        merged_df = _merge_existing_iamc_table(connection, table_name, df, index_columns)
        merged_df.to_sql(table_name, connection, if_exists='replace', index=False)
        connection.commit()
    finally:
        connection.close()

    excel_path = output_directory / f'{table_name}.xlsx'
    merged_df.to_excel(excel_path, index=False)


def _merge_existing_iamc_table(
    connection: sqlite3.Connection,
    table_name: str,
    new_df: pd.DataFrame,
    index_columns: list[str],
) -> pd.DataFrame:
    try:
        existing_df = pd.read_sql_query(f'SELECT * FROM `{table_name}`', connection)
    except (sqlite3.OperationalError, pd.errors.DatabaseError):
        return new_df

    if existing_df.empty:
        return new_df

    # SQLite always returns column names as strings, but pivot_iamc_wide_table produces
    # int year columns. Without normalizing, int 2025 and str "2025" are treated as distinct
    # columns by Index.union()/reindex(), producing duplicate "2025" columns once both are
    # written back to SQL as strings (sqlite3.OperationalError: duplicate column name).
    existing_df = existing_df.rename(columns=lambda c: int(c) if isinstance(c, str) and c.isdigit() else c)
    if new_df.empty:
        return existing_df

    existing_indexed = existing_df.set_index(index_columns)
    new_indexed = new_df.set_index(index_columns)
    kept_existing = existing_indexed.loc[~existing_indexed.index.isin(new_indexed.index)]
    all_columns = kept_existing.columns.union(new_indexed.columns)
    kept_existing = kept_existing.reindex(columns=all_columns)
    new_indexed = new_indexed.reindex(columns=all_columns)
    return pd.concat([kept_existing, new_indexed]).reset_index()


def _normalize_year(value: object) -> int:
    if isinstance(value, int):
        return value

    year_text = str(value)
    year_text = year_text.removeprefix('Y')
    return int(year_text)
