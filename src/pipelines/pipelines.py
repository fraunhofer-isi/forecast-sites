# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import json
from pathlib import Path

import geopandas


class Pipelines:
    def __init__(self):
        file_path = './resources/input/pipelines.geojson'
        self.file_path = file_path
        self.pipelines_df = geopandas.read_file(file_path)
        self.pipelines_json = self._read_pipelines_as_json(file_path)
        self.pipeline_indices = self.pipelines_df.index
        self.modes = ['' for _pipeline in self.pipeline_indices]
        self.pipeline_line_strings = list(self.pipelines_df['geometry'])

    @staticmethod
    def _read_pipelines_as_json(file_path):
        with Path(file_path).open(encoding='utf8') as f:
            json_features = json.load(f)
            return json_features

    def update_modes(self, year):
        self.modes = []
        for pipeline_index in self.pipeline_indices:
            pipeline_row = self.pipelines_df.loc[pipeline_index]
            reference_year = pipeline_row['Commissioning Year First']
            if year >= reference_year:
                self.pipelines_df.loc[self.pipelines_df['id'] == pipeline_index, 'mode'] = 'H2'

        for feature in self.pipelines_json['features']:
            properties = feature['properties']
            reference_year = properties['Commissioning Year First']
            if year >= reference_year:
                properties['mode'] = 'H2'
                properties['color'] = 'limegreen'
                feature['properties'] = properties
            mode = feature['properties']['mode']
            self.modes.append(mode)
