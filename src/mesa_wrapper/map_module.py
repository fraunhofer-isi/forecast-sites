# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import json
import pathlib
from typing import ClassVar

from mesa_viz_tornado.ModularVisualization import VisualizationElement


class MapModule(VisualizationElement):
    """A MapModule for Leaflet maps."""

    package_includes: ClassVar[list] = []

    local_includes: ClassVar[list[str]] = [
        'web/node_modules/jquery/dist/jquery.min.js',
        'web/node_modules/leaflet/dist/leaflet.js',
        'web/node_modules/leaflet/dist/leaflet.css',
        'web/src/leafletMap.js',
    ]

    def __init__(
        self,
        simulation_options,
        portrayal_method,
        view=None,
        zoom=10,
        map_height=500,
        map_width=500,
    ):
        super().__init__()
        self._simulation_options = simulation_options
        self.portrayal_method = portrayal_method
        self.map_height = map_height
        self.map_width = map_width
        self.view = self._initialize_view(view)
        self.js_code = self._javascript_code(zoom, map_height, map_width)

    @staticmethod
    def _initialize_view(view):
        if view is None:
            view = [0, 0]
        return view

    @staticmethod
    def _store_feature_collection_as_json(feature_collection, file_path):
        json_content = json.dumps(feature_collection)
        with pathlib.Path(file_path).open('w', encoding='utf8') as f:
            f.write(json_content)

    @staticmethod
    def _include_pipelines(feature_collection, model):
        for pipeline in model.pipelines.pipelines_json['features']:
            feature_collection['features'].append(pipeline)
        return feature_collection

    def render(self, model):
        feature_collection = self._feature_collection(model)
        output_directory = self._simulation_options['output_directory']
        self._store_feature_collection_as_json(feature_collection, output_directory + '/data.json')
        return feature_collection

    def _javascript_code(
        self,
        zoom,
        map_height,
        map_width,
    ):
        new_element = 'new MapModule({}, {}, {}, {})'
        new_element = new_element.format(self.view, zoom, map_width, map_height)
        code = 'elements.push(' + new_element + ');'
        return code

    def _feature_collection(self, model):
        feature_collection = {
            'type': 'FeatureCollection',
            'features': [],
        }

        feature_collection = self._include_pipelines(feature_collection, model)
        feature_collection = self._include_agents(feature_collection, model)

        return feature_collection

    def _include_agents(self, feature_collection, model):
        for _, agent in enumerate(model.grid.agents):
            raw_shape = agent.__geo_interface__()
            shape = raw_shape.copy()
            shape['properties']['_crs'] = None  # we remove the CRS object because it would not be serializable
            portrayal = self.portrayal_method(agent)

            for key, value in portrayal.items():
                shape['properties'][key] = value
            # feature_collection is mutated in place: accumulate all agents' geometries in a single collection
            feature_collection['features'].append(shape)

        return feature_collection
