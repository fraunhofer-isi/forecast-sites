# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
from mesa_geo.geoagent import GeoAgent
from shapely import geometry as shapley_geometry
from shapely import ops


class SiteAgent(GeoAgent):
    def __init__(
        self,
        model,
        geometry,
        crs,
        region_id,
        site,
    ):
        super().__init__(model, geometry, crs)
        self.region_id = region_id
        self.site = site

    def step(self):
        simulation = self.model
        year = simulation.year
        simulation_mode = simulation.simulation_mode
        co2_cost_in_euro_per_ton_co2 = simulation.regions[self.region_id].co2_cost_in_euro_per_ton_c02(year)
        if simulation.recognize_pipelines:
            distance_to_closest_h2_pipeline = self.get_distance_to_closest_h2_pipeline()
        else:
            distance_to_closest_h2_pipeline = 0
        pipeline_cost_scaling = self.pipeline_cost_scaling(distance_to_closest_h2_pipeline)
        self.site.process_year(
            year,
            simulation_mode,
            co2_cost_in_euro_per_ton_co2,
            pipeline_cost_scaling,
            distance_to_closest_h2_pipeline,
        )

    def pipeline_cost_scaling(self, distance_to_closest_h2_pipeline):
        simulation = self.model
        if simulation.recognize_pipelines:
            distance = distance_to_closest_h2_pipeline

            if distance is None:
                pipeline_cost_scaling = 10e12
            else:
                pipeline_cost_scaling = 100 * distance

        else:
            pipeline_cost_scaling = 1
        return pipeline_cost_scaling

    def get_distance_to_closest_h2_pipeline(self):
        simulation = self.model
        if simulation.recognize_pipelines:
            site_pipeline_indices = simulation.pipeline_site_relations.index.get_level_values('site') == self.unique_id
            site_pipeline_relation = simulation.pipeline_site_relations.loc[site_pipeline_indices]
            site_pipeline_h2 = site_pipeline_relation.groupby('mode')
            site_pipeline_number_of_groups = site_pipeline_h2.ngroups
            required_group_size = 2
            if site_pipeline_number_of_groups == required_group_size:
                h2_group = site_pipeline_h2.get_group('H2')
                closest_h2_pipeline = h2_group.sort_values(by='distance').head(1)
                closest_h2_pipeline_distance = closest_h2_pipeline['distance'].to_numpy()[0]
            else:
                closest_h2_pipeline_distance = None
        else:
            closest_h2_pipeline_distance = None
        return closest_h2_pipeline_distance

    @staticmethod
    def sigmoid(distance, maximum_value, steepness, x_midpoint, offset):
        s = maximum_value / (1 + np.exp(-steepness * (distance - x_midpoint))) + offset
        return s

    def __geo_interface__(self):
        """
        Override the default __geo_interface__ method of GeoAgent to resolve some serialization issues.

        Return a GeoJSON Feature.

        Removes shape from attributes.
        """
        simulation = self.model
        properties = dict(vars(self))
        properties['model'] = str(simulation)
        geometry = properties.pop('geometry')
        properties.pop('site')  # <= removes site because it is not serializable
        geometry = ops.transform(simulation.grid.transformer.transform, geometry)
        return {'type': 'Feature', 'geometry': shapley_geometry.mapping(geometry), 'properties': properties}
