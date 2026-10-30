# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pandas as pd

from utils import data_frame_utils


def test_years():
    df = pd.DataFrame(
        {
            'id': [1],
            'Y2020': [10],
            'Y2021': [15],
            'value': [100],
        }
    )
    result = data_frame_utils.years(df)
    assert result == [2020, 2021]


def test_rename_year_columns():
    df = pd.DataFrame(
        {
            'id': [1],
            'Y2020': [10],
            'Y2021': [15],
            'value': [100],
        }
    )

    result = data_frame_utils.rename_year_columns(df)
    assert '2020' in result.columns
    assert '2021' in result.columns
    assert 'Y2020' not in result.columns
    assert 'Y2021' not in result.columns


def test_index_columns():
    df = pd.DataFrame(
        {
            'id': [1],
            'id_scenario': [2],
            'id_process': [2],
            'value': [100],
        }
    )
    result = data_frame_utils.index_columns(df)
    assert result == ['id_scenario', 'id_process']


def test_ensure_year_columns_exist():
    df = pd.DataFrame(
        {
            'id': [1],
            'Y2020': [10],
            'value': [100],
        }
    )
    expected_years = [2020, 2021, 2022]
    result = data_frame_utils.ensure_year_columns_exist(df, expected_years)
    assert 'Y2020' in result.columns
    assert 'Y2021' in result.columns
    assert 'Y2022' in result.columns
    assert result['Y2021'].isna().all()
    assert result['Y2022'].isna().all()


def test_reverse_sign_of_value_columns():
    df = pd.DataFrame(
        {
            'id': [1, 2],
            'id_scenario': [1, 1],
            'value1': [100, -50],
            'value2': [-200, 75],
        }
    )
    result = data_frame_utils.reverse_sign_of_value_columns(df)
    assert result['value1'].tolist() == [-100, 50]
    assert result['value2'].tolist() == [200, -75]
    assert result['id'].tolist() == [1, 2]
    assert result['id_scenario'].tolist() == [1, 1]


def test_reverse_sign_with_non_numeric_columns():
    """Test that non-numeric columns are left unchanged."""
    df = pd.DataFrame(
        {
            'id': [1, 2],
            'name': ['product_a', 'product_b'],
            'value': [100, -50],
        }
    )
    result = data_frame_utils.reverse_sign_of_value_columns(df)
    # Numeric column should be reversed
    assert result['value'].tolist() == [-100, 50]
    # Non-numeric column should be unchanged
    assert result['name'].tolist() == ['product_a', 'product_b']
    # ID column should be unchanged
    assert result['id'].tolist() == [1, 2]
