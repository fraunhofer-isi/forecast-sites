# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import shapely
from mesa_geo.geoagent import GeoAgent


class SiteAgent(GeoAgent):
    def __init__(
        self,
        model,
        geometry,
        crs,
        id_region,
        site,
    ):
        super().__init__(model, geometry, crs)
        self._region = model.regions[id_region]
        self._site = site
        simulation = model
        self._site.initialize_context(simulation)

    @property
    def used_process_ids(self):
        process_ids = self._site.used_process_ids
        return process_ids

    def step(self):
        simulation = self.model
        self._site.initialize_context(simulation)

        if simulation.options['optimization_type'].is_region_scoped:
            return

        year = simulation.year
        self._site.optimize(year)

    @staticmethod
    def _geojson_geometry(geometry, simulation):
        transform_function = simulation.grid.transformer.transform
        transformed_geometry = shapely.ops.transform(transform_function, geometry)
        geojson_geometry = shapely.geometry.mapping(transformed_geometry)
        return geojson_geometry

    def __geo_interface__(self):
        """
        Override the default __geo_interface__ method of GeoAgent to resolve some serialization issues.

        Return a GeoJSON Feature.

        Removes shape from attributes.
        """
        simulation = self.model
        properties = self._properties(simulation)

        geometry = properties.pop('geometry')
        geojson_geometry = self._geojson_geometry(geometry, simulation)

        feature = {
            'type': 'Feature',
            'properties': properties,
            'geometry': geojson_geometry,
        }
        return feature

    def _properties(self, simulation):
        properties = dict(vars(self))
        properties.pop('_region')  # <= removes region because it is not serializable
        properties.pop('_site')  # <= removes site because it is not serializable
        properties['model'] = str(simulation)
        return properties
