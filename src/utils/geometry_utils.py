# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from shapely.geometry.linestring import LineString

logger = logging.getLogger(__name__)


def remove_duplicate_points(line, context_object_for_debugging, data_file_path):
    coordinates = []

    for coord in line.coords:
        if coord in coordinates:
            context = _context(context_object_for_debugging)
            message = (
                f'Duplicate coordinate {coord} found in LineString. '
                f'Please fix the source data in {data_file_path} '
                f'by removing the duplicate coordinate. '
                f'Context:\n{context}'
            )
            logger.warning(message)
        else:
            coordinates.append(coord)
    cleaned_line_string = LineString(coordinates)
    return cleaned_line_string


def _context(pipeline):
    pipeline_string = str(pipeline)
    context = ' '.join(pipeline_string.split())
    return context
