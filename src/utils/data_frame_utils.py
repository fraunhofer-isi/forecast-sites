# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pandas as pd


def years(df):
    """
    Extract years from year columns of the data frame.

    Some of the column names start with Y, e.g. "Y2020". This function extracts the years from those column names.
    """
    numeric_years = [int(column[1:]) for column in df.columns if column.startswith('Y')]
    return numeric_years


def rename_year_columns(df):
    """Rename year columns starting with Y, for example Y2020 => 2020"""
    renamed_df = df.rename(
        columns=lambda x: x.replace('Y', '') if x.startswith('Y') else x,
    )
    return renamed_df


def index_columns(df):
    column_names = [column_name for column_name in df.columns if column_name.startswith('id_')]
    return column_names


def ensure_year_columns_exist(df, expected_years):
    for year in expected_years:
        column_name = f'Y{year}'
        if column_name not in df.columns:
            df[column_name] = [None] * len(df)
    df = df.sort_index(axis=1)
    return df


def reverse_sign_of_value_columns(df):
    """
    Return a copy of df with the sign of value (non id) numeric columns reversed.

    Identifier columns (starting with 'id_' or named exactly 'id') are left unchanged.
    Only numeric columns are negated to avoid altering non-numeric data.
    """
    id_cols = set(index_columns(df))
    id_cols.add('id')
    result = df.copy()
    for col in result.columns:
        if col in id_cols:
            continue
        if pd.api.types.is_numeric_dtype(result[col]):
            result[col] = -1 * result[col]
    return result
