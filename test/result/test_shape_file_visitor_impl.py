# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from pathlib import Path

from test_utils.isi_mock import Mock

from result.shape_file_visitor import ShapeFileVisitor


def test_empty_hooks_and_finalize_return_none(tmp_path):
    visitor = ShapeFileVisitor({'output_directory': str(tmp_path)})

    assert visitor.enter_site(object(), 2030) is None
    assert visitor.enter_production_unit(object(), 2030) is None
    assert visitor.enter_sub_production_unit(object(), 2030) is None
    assert visitor.finalize() is None


def test_shape_file_path_creates_folder_and_returns_expected_file(tmp_path):
    visitor = ShapeFileVisitor({'output_directory': str(tmp_path)})
    region_mock = Mock()
    region_mock.id_scenario = 3

    shape_path = visitor._shape_file_path(region_mock, 2035)

    assert shape_path.endswith('shape_file_2035_scenario_3/forecast_sites.shp')
    assert (Path(tmp_path) / 'shape_file_2035_scenario_3').is_dir()
