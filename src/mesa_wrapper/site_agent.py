# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
from mesa_geo.geoagent import GeoAgent
from shapely import geometry as shapley_geometry
from shapely import ops


class SiteAgent(GeoAgent):

    def __init__(self, model, geometry, crs, region_id, site):
        super().__init__(model, geometry, crs)
        self.region_id = region_id
        self.site = site

    def step(self):
        year = self.model.year
        simulation_mode = self.model.simulation_mode
        co2_cost_in_euro_per_ton_co2 = self.model.regions[self.region_id].co2_cost_in_euro_per_ton_c02(year)
        if self.model.recognize_pipelines:
            distance_to_closest_H2_pipeline = self.get_distance_to_closest_H2_pipeline()
        else:
            distance_to_closest_H2_pipeline = 0
        pipeline_cost_scaling = self.pipeline_cost_scaling(distance_to_closest_H2_pipeline)
        self.site.process_year(
            year,
            simulation_mode,
            co2_cost_in_euro_per_ton_co2,
            pipeline_cost_scaling,
            distance_to_closest_H2_pipeline,
        )

    def pipeline_cost_scaling(self, distance_to_closest_H2_pipeline):
        if self.model.recognize_pipelines:
            distance = distance_to_closest_H2_pipeline

            if distance is not None:
                # pipeline_cost_scaling = 100 * distance
                pipeline_cost_scaling = 100000000000000
            else:
                pipeline_cost_scaling = (10e6) ** 2
                # pipeline_cost_scaling = 1000000000
        else:
            pipeline_cost_scaling = 1
        return pipeline_cost_scaling

    def get_distance_to_closest_H2_pipeline(self):
        if self.model.recognize_pipelines:
            site_pipeline_indices = self.model.pipeline_site_relations.index.get_level_values('site') == self.unique_id
            site_pipeline_relation = self.model.pipeline_site_relations.loc[site_pipeline_indices]
            site_pipeline_H2 = site_pipeline_relation.groupby('mode')
            site_pipeline_number_of_groups = site_pipeline_H2.ngroups
            if site_pipeline_number_of_groups == 2:
                H2_group = site_pipeline_H2.get_group('H2')
                closest_H2_pipeline = H2_group.sort_values(by='distance').head(1)
                closest_H2_pipeline_distance = closest_H2_pipeline['distance'].to_numpy()[0]
            else:
                closest_H2_pipeline_distance = None
        else:
            closest_H2_pipeline_distance = None
        return closest_H2_pipeline_distance

    @staticmethod
    def sigmoid(distance, L, k, x0, offset):
        s = L / (1 + np.exp(-k * (distance - x0))) + offset
        return s

    def __geo_interface__(self):
        """Override the default __geo_interface__ method of GeoAgent to resolve some serialization issues.

        Return a GeoJSON Feature.

        Removes shape from attributes.
        """
        properties = dict(vars(self))
        properties["model"] = str(self.model)
        geometry = properties.pop("geometry")
        properties.pop("site")  # <= removes site because it is not serializable
        geometry = ops.transform(self.model.grid.transformer.transform, geometry)
        return {"type": "Feature", "geometry": shapley_geometry.mapping(geometry), "properties": properties}
