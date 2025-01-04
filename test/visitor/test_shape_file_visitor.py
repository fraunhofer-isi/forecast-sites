# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import MagicMock, patch

from visitor.shape_file_visitor import ShapeFileVisitor


@pytest.fixture
def sut():
    with patch('utils.file_utils.create_folder_if_not_exists'):
        return ShapeFileVisitor()


def test_visit_region(sut):
    sut._export_sites_to_shape_file = MagicMock
    sut.visit_region(region=MagicMock(), year=2020)
    assert sut._export_sites_to_shape_file.called


def test_visit_site(sut):
    sut.visit_site(site=MagicMock(), year=2020)
    assert True


def test_production_unit(sut):
    sut.visit_production_unit(production_unit=MagicMock(), year=2020)
    assert True


def test_visit_product(sut):
    sut.visit_product(product=MagicMock(), year=2020)
    assert True


def test_visit_process(sut):
    sut.visit_process(process=MagicMock(), year=2020)
    assert True


def test_finalize(sut):
    sut.finalize()
    assert True


class TestExportSitesToShapeFile:
    site_df = pd.DataFrame(
        {
            'id': [1],
            'id_region': [10],
            'id_company': [100],
            'latitude': [5],
            'longitude': [50],
            'co2_equivalent_2015_in_tons': [1000],
            'geometry': [None],
        }
    )
    site_df.set_index(['id'], inplace=True)

    def test_empty_data_frame(self, sut):
        sut._check_export_column_names = MagicMock()
        sut._prepare_shape_file_path = MagicMock()

        site_df = self.site_df[0:0]
        region_mock = MagicMock()
        region_mock.site_df = lambda: site_df

        with patch('utils.collection_utils.join_with_comma') as patched_join:
            with patch('utils.file_utils.delete_file_if_exists') as patched_delete:
                sut._export_sites_to_shape_file(region_mock, year=2020)

                assert patched_join.called
                assert sut._check_export_column_names.called
                assert sut._prepare_shape_file_path.called
                assert patched_delete.called

    def test_non_empty_data_frame(self, sut):
        sut._check_export_column_names = MagicMock()
        sut._prepare_shape_file_path = MagicMock()

        site_df = self.site_df
        site_df.to_file = MagicMock()

        region_mock = MagicMock()
        region_mock.site_df = lambda: site_df

        with patch('utils.collection_utils.join_with_comma', return_value='mocked_process_ids') as patched_join:
            sut._export_sites_to_shape_file(region_mock, year=2020)

            assert patched_join.called
            assert sut._check_export_column_names.called
            assert sut._prepare_shape_file_path.called
            assert site_df.to_file.called


def test__prepare_shape_file_path(sut):
    with patch('utils.file_utils.create_folder_if_not_exists') as patched_create_folder:
        result = sut._prepare_shape_file_path(year=2020)
        assert result == '../output/shape_file_2020/technology_diffusion.shp'


def test__check_export_column_names(sut):
    data_frame = pd.DataFrame({'a_long_column_name': [1]})
    with patch('builtins.print') as patched_print:
        sut._check_export_column_names(data_frame)
        assert patched_print.called
