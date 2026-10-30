# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from shapely.geometry.linestring import LineString
from test_utils.isi_mock import Mock, patch

from utils import geometry_utils


@patch(geometry_utils._context, 'pipeline\ninfo')
def test_remove_duplicate_points(caplog):
    line = LineString([(0, 0), (0, 0), (1, 1), (1, 1), (2, 2)])
    data_file_path = 'some/data/file.geojson'

    context_object_for_debugging = Mock()
    with caplog.at_level('WARNING', logger='utils.geometry_utils'):
        result = geometry_utils.remove_duplicate_points(line, context_object_for_debugging, data_file_path)

    assert result == LineString([(0, 0), (1, 1), (2, 2)])
    assert data_file_path in caplog.text
    assert 'fix the source data' in caplog.text


def test_context():
    pipeline = Mock()
    pipeline.__str__.return_value = 'pipeline\ninfo'
    result = geometry_utils._context(pipeline)

    assert result == 'pipeline info'
