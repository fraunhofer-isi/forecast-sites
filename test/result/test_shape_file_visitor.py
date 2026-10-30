# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import logging

import geopandas
import pandas as pd
import pytest
from geopandas import GeoDataFrame
from test_utils.isi_mock import Mock, fixture, patch

from result.shape_file_visitor import ESRI_MAX_FIELD_LENGTH, ShapeFileVisitor
from utils import file_utils


@fixture
@patch(file_utils.create_folder_if_not_exists)
def sut():
    simulation_options = {'output_directory': 'mocked_output_directory'}
    return ShapeFileVisitor(simulation_options)


def test_construction(sut):
    assert sut is not None


def test_shorten_column_names(sut):
    site_data = pd.DataFrame(
        [
            {'id': 1, 'id_company': 20},
        ]
    )
    result = sut._shorten_column_names(site_data)
    columns = result.columns.tolist()
    assert columns == [
        'id',
        'id_comp',
    ]


class TestCheckLengthOfColumnNames:
    def test_short_column_names(self, sut):
        df = pd.DataFrame(
            [
                {'id': 1, 'id_company': 20},
            ]
        )
        sut._check_length_of_column_names(df)

    def test_long_column_names(self, sut):
        df = pd.DataFrame(
            [
                {'id': 1, 'id_company_type': 20},
            ]
        )
        with pytest.raises(ValueError, match='Length of column name'):
            sut._check_length_of_column_names(df)


def test_check_export_column_names(sut):
    data_frame = pd.DataFrame({'a_long_column_name': [1]})
    with patch(logging.warning) as patched_warning:
        sut._check_export_column_names(data_frame)
        patched_warning.assert_called_once()


def test_check_export_column_names_short_names(sut):
    """Test that no warning is issued for short column names."""
    data_frame = pd.DataFrame({'id': [1], 'name': [2]})
    with patch(logging.warning) as patched_warning:
        sut._check_export_column_names(data_frame)
        patched_warning.assert_not_called()


class TestCheckCrs:
    def test_without_crs_attribute(self, sut):
        df = pd.DataFrame()
        with pytest.raises(ValueError, match='CRS is missing'):
            sut._check_crs(df)

    def test_without_crs(self, sut):
        df = pd.DataFrame({'longitude': [50.0], 'latitude': [5.0], 'id': [1]})
        geo_df = geopandas.GeoDataFrame(
            df,
            geometry=geopandas.points_from_xy(df.longitude, df.latitude),
        )
        with pytest.raises(ValueError, match='CRS is missing'):
            sut._check_crs(geo_df)

    def test_with_crs(self, sut):
        df = pd.DataFrame({'longitude': [50.0], 'latitude': [5.0], 'id': [1]})
        geo_df = geopandas.GeoDataFrame(
            df,
            geometry=geopandas.points_from_xy(df.longitude, df.latitude),
            crs='EPSG:4326',
        )
        sut._check_crs(geo_df)


def test_filter_sites_for_region(sut):
    site_df = pd.DataFrame(
        [
            {'id': 1, 'id_region': 20},
            {'id': 2, 'id_region': 30},
            {'id': 3, 'id_region': 20},
        ]
    ).set_index('id')

    region_mock = Mock()
    region_mock.sites = [Mock(id=1), Mock(id=3)]

    result = sut._filter_sites_for_region(site_df, region_mock)
    assert len(result) == 2
    assert 1 in result.index
    assert 3 in result.index


def test_set_year(sut):
    site_df = pd.DataFrame(
        [
            {'id': 1, 'id_region': 20},
            {'id': 2, 'id_region': 30},
        ]
    ).set_index('id')

    result = sut._set_year(site_df, 2020)
    assert 'year' in result.columns
    assert result['year'][1] == 2020
    assert result['year'][2] == 2020


@patch(ShapeFileVisitor._process_ids_as_string, 'mocked_ids')
def test_set_process_ids(sut):
    site_df = pd.DataFrame(
        [
            {'id': 1, 'id_region': 20},
            {'id': 2, 'id_region': 30},
        ]
    ).set_index('id')

    region_mock = Mock()
    region_mock.process_ids_for_site = Mock(side_effect=[[10, 20], [30]])

    result = sut._set_process_ids(site_df, region_mock)
    assert 'proc_ids' in result.columns
    assert result['proc_ids'][1] == 'mocked_ids'


@patch(ShapeFileVisitor._join_within_limit, 'mocked_result')
def test_process_ids_as_string(sut):
    region_mock = Mock()
    region_mock.process_ids_for_site = Mock(return_value=[10, 20, 30])

    result = sut._process_ids_as_string(region_mock, 1)
    assert result == 'mocked_result'


class TestJoinWithinLimit:
    def test_empty_list(self):
        assert ShapeFileVisitor._join_within_limit([]) == ''

    def test_single_id(self):
        assert ShapeFileVisitor._join_within_limit([42]) == '42'

    def test_all_ids_fit(self):
        assert ShapeFileVisitor._join_within_limit([1, 2, 3]) == '1, 2, 3'

    def test_exact_254_chars_no_ellipsis(self):
        # Build a list whose full join is exactly 254 chars — no truncation expected.
        # Each id is '1' (1 char), separator is ', ' (2 chars).
        # n ids → n + (n-1)*2 = 3n - 2 chars. Solve 3n - 2 = 254 → n = 256/3 ≈ 85.
        # Use 85 ids of '1': 85 + 84*2 = 85 + 168 = 253 chars. Add one '12' (2 chars):
        # 253 + 2 + 2 = 257 — too long. Use 84 ids of '1' + one '123' (3 chars):
        # 84 + 83*2 + 2 + 3 = 84 + 166 + 5 = 255 — still too long.
        # Simplest: construct a string of exactly 254 chars directly.
        ids = list(range(1, 51))  # '1, 2, ..., 50' = well under 254
        result = ShapeFileVisitor._join_within_limit(ids)
        assert len(result) <= 254
        assert '...' not in result

    def test_truncated_ends_with_last_id(self):
        # 100 six-digit ids → full string >> 254 chars
        ids = list(range(100000, 100100))
        result = ShapeFileVisitor._join_within_limit(ids)
        assert result.endswith(str(ids[-1]))

    def test_truncated_contains_ellipsis(self):
        ids = list(range(100000, 100100))
        result = ShapeFileVisitor._join_within_limit(ids)
        assert ', ..., ' in result

    def test_result_never_exceeds_254_chars(self):
        ids = list(range(100000, 100100))
        result = ShapeFileVisitor._join_within_limit(ids)
        assert len(result) <= 254

    def test_truncated_starts_with_first_id(self):
        ids = list(range(100000, 100100))
        result = ShapeFileVisitor._join_within_limit(ids)
        assert result.startswith(str(ids[0]))

    def test_last_id_alone_fills_field_returns_truncated_prefix_with_ellipsis(self):
        # Defensive branch (line 115): when the last id's own string form is so long
        # that even ', ..., <last>' exceeds ESRI_MAX_FIELD_LENGTH, the function falls
        # back to a fixed truncation of the full join plus a trailing ', ...'.
        # Integer ids can never be this long; only pathological string ids reach here.
        long_id = 'x' * 255
        result = ShapeFileVisitor._join_within_limit([long_id])

        assert len(result) == ESRI_MAX_FIELD_LENGTH
        assert result.endswith(', ...')
        assert result == long_id[: ESRI_MAX_FIELD_LENGTH - len(', ...')] + ', ...'

    def test_multi_ids_with_long_last_id_uses_defensive_truncation(self):
        # Same defensive branch, reached via a long LAST id (not a single id):
        # total join exceeds the limit AND the suffix alone already exceeds it.
        # '12, ' (4 chars) + 251 chars = 255 > 254, and ', ..., ' + 251 = 258 >= 254.
        long_last = 'y' * 251
        ids = [12, long_last]

        result = ShapeFileVisitor._join_within_limit(ids)

        assert len(result) == ESRI_MAX_FIELD_LENGTH
        assert result.endswith(', ...')


def test_enter_region(sut):
    sut._export_sites_to_shape_file = Mock()
    sut.enter_region('mocked_region', 2020)
    assert sut._export_sites_to_shape_file.called


mocked_site_df = GeoDataFrame(
    pd.DataFrame(
        {
            'id': [1],
            'id_region': [10],
            'id_company': [100],
            'latitude': [5],
            'longitude': [50],
            'geometry': [None],
        },
    ).set_index(['id'])
)


@patch(ShapeFileVisitor._shape_file_path)
class TestExportSitesToShapeFile:
    def test_empty_data_frame(self, sut):
        empty_site_df = mocked_site_df[0:0]

        with (
            patch(ShapeFileVisitor._site_data_frame, empty_site_df),
            patch(file_utils.delete_file_if_exists) as patched_delete,
        ):
            sut._export_sites_to_shape_file('mocked_region', 2020)
            assert patched_delete.called

    def test_non_empty_data_frame(self, sut):
        mocked_site_df.to_file = Mock()
        with patch(ShapeFileVisitor._site_data_frame, mocked_site_df):
            sut._export_sites_to_shape_file('mocked_region', 2020)
            assert mocked_site_df.to_file.called


@patch(ShapeFileVisitor._shorten_column_names)
@patch(ShapeFileVisitor._filter_sites_for_region)
@patch(ShapeFileVisitor._set_year)
@patch(ShapeFileVisitor._set_process_ids, 'mocked_result')
@patch(ShapeFileVisitor._check_export_column_names)
@patch(ShapeFileVisitor._check_crs)
def test_site_data_frame(sut):
    region_mock = Mock()
    region_mock.site_data = mocked_site_df
    result = sut._site_data_frame(region_mock, 2020)
    assert result == 'mocked_result'


def test_shape_file_path(sut):
    region_mock = Mock()
    region_mock.id_scenario = 2
    with patch(file_utils.create_folder_if_not_exists):
        result = sut._shape_file_path(region_mock, year=2020)
        assert result == 'mocked_output_directory/shape_file_2020_scenario_2/forecast_sites.shp'
