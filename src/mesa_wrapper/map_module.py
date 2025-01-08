# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
from pathlib import Path

from mesa_viz_tornado.ModularVisualization import VisualizationElement


class MapModule(VisualizationElement):
    """A MapModule for Leaflet maps."""

    package_includes = []

    local_includes = [
        'web/node_modules/jquery/dist/jquery.min.js',
        'web/node_modules/leaflet/dist/leaflet.js',
        'web/node_modules/leaflet/dist/leaflet.css',
        'web/src/leafletMap.js',
    ]

    def __init__(
        self,
        portrayal_method,
        view=None,
        zoom=10,
        map_height=500,
        map_width=500,
    ):
        super().__init__()
        self.portrayal_method = portrayal_method
        self.map_height = map_height
        self.map_width = map_width

        if view is None:
            view = [0, 0]
        self.view = view

        new_element = "new MapModule({}, {}, {}, {})"
        new_element = new_element.format(view, zoom, map_width, map_height)
        self.js_code = "elements.push(" + new_element + ");"

    def render(self, model):
        feature_collection = self._extract_serializable_json(model)

        j = json.dumps(feature_collection)
        with Path('data.json').open('w') as f:
            f.write(j)
        return feature_collection

    def _extract_serializable_json(self, model):
        feature_collection = {
            'type': "FeatureCollection",
            'features': [],
        }

        feature_collection = self._include_pipelines(feature_collection, model)
        feature_collection = self._include_agents(feature_collection, model)

        return feature_collection

    @staticmethod
    def _include_pipelines(feature_collection, model):
        for pipeline in model.pipelines.pipelines_json['features']:
            feature_collection["features"].append(pipeline)
        return feature_collection

    def _include_agents(self, feature_collection, model):
        for _, agent in enumerate(model.grid.agents):
            shape = agent.__geo_interface__()
            shape_info = shape.copy()
            shape_info['properties']['_crs'] = None  # we remove the CRS object because it would not be serializable
            portrayal = self.portrayal_method(agent)

            for key, value in portrayal.items():
                shape_info["properties"][key] = value
                feature_collection["features"].append(shape_info)

        return feature_collection
