# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from pathlib import Path

import geopandas


class Pipelines:

    def __init__(self):
        file_path = './src/pipelines/pipelines.geojson'
        with Path(file_path).open() as f:
            self.pipelines_json = json.load(f)
        self.pipelines_df = geopandas.read_file(file_path)

        self.pipeline_indices = self.pipelines_df.index
        self.modes = ['' for _pipeline in self.pipeline_indices]
        self.pipeline_line_strings = list(self.pipelines_df['geometry'])
        print('pipelines_df in __init__')
        print(self.pipelines_df['id'])
        print('pipeline_df after initialization')
        print(self.pipelines_df.columns)

    def update_mode(self, year):
        self.modes = []
        for pipeline_index in self.pipelines_df.index:
            if year >= self.pipelines_df.loc[pipeline_index]['Commissioning Year First']:
                print('in update_mode function: self.pipelines_df')
                print(self.pipelines_df)
                self.pipelines_df.loc[self.pipelines_df["id"] == pipeline_index, "mode"] = 'H2'
                print('after setting mode')
                print(self.pipelines_df.loc[pipeline_index])

        for feature in self.pipelines_json['features']:
            if year >= feature['properties']['Commissioning Year First']:
                feature['properties']['mode'] = 'H2'
                feature['properties']['color'] = 'limegreen'
            self.modes.append(feature['properties']['mode'])
