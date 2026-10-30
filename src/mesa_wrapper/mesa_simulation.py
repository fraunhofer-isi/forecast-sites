# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import random
from math import asin, cos, pi, sqrt

import pandas as pd
from mesa import Model
from mesa.datacollection import DataCollector
from mesa_geo import AgentCreator, GeoSpace

from mesa_wrapper.site_agent import SiteAgent
from pipelines.pipelines import Pipelines
from utils import geometry_utils
from utils.site_cluster import first_digit
from utils.time_utils import create_time_span


class MesaSimulation(Model):
    COORDINATE_REFERENCE_SYSTEM = 'epsg:4326'

    def __init__(
        self,
        regions,
        options,
        visitors,
    ):
        Model.__init__(self)
        self.regions = regions
        self.options = options
        self._visitors = visitors

        self._time_span = self._create_time_span()

        # do not rename following model properties; they are required by mesa server
        self.random = random.Random()
        self.grid = GeoSpace(MesaSimulation.COORDINATE_REFERENCE_SYSTEM)
        self.datacollector = self._create_data_collector()
        self.running = True
        self.is_recognizing_pipelines = True

        self.pipelines = Pipelines()
        self.pipeline_site_relations = self._pipeline_site_relations()

        self._create_site_agents()

        self._initialize_start_year()

    @property
    def year(self):
        zero_based_time_index = self.steps
        year = self._time_span[zero_based_time_index]
        return year

    @property
    def _last_year(self):
        last_year = self._time_span[-1]
        return last_year

    @staticmethod
    def _create_data_collector():
        branch_reporters = {
            f'Branch {b}': (
                lambda sim, branch=b: sum(1 for a in sim.agents if any(first_digit(pid) == branch for pid in a.used_process_ids))
            )
            for b in range(1, 10)
        }
        return DataCollector(
            model_reporters={
                'agent_count': lambda sim: len(sim.agents),
                **branch_reporters,
            },
            agent_reporters={'process_ids': lambda a: a.used_process_ids},
        )

    def step(self):
        super().step()
        # represents a single time step / year of the simulation
        # The start year has already been initialized in the constructor.
        # So here we only need to handle the following years.

        year = self.year

        # * The following command calls the step functions of all agent instances, see site_agent.step
        # * Furthermore, the site_agent's step function delegates optimization work to
        # site.optimize => production_unit.optimize
        # * The production_unit's optimize function immediately applies it's optimization results,
        # see production_unit._apply_results
        # * Applying the results means that the production_unit:
        # - creates or updates it's sub_production_units
        # - provides or consumes carriers for the current year
        if self.options['optimization_type'].is_region_scoped:
            self._optimize_regions(year)
        else:
            self.agents.do('step')

        # result analysis is done after the object hierarchy has been updated for the current year:
        self._accept_visitors(year)
        self.datacollector.collect(self)

        self._update_pipelines()

        self._end_simulation_after_last_year(year)
        self._finalize_visitors_if_finished()

    def _initialize_start_year(self):
        start_year = self.year
        optimize_start_year = self.options.get('optimize_start_year', False)

        if optimize_start_year:
            if self.options['optimization_type'].is_region_scoped:
                self._optimize_regions(start_year)
            else:
                # Optimization handles carrier consumption/provision itself
                self.agents.do('step')
        else:
            # Default: read carrier amounts directly from installed processes
            self._consume_purchased_carrier_amounts_for_start_year(start_year)

        self._accept_visitors(start_year)

    def _optimize_regions(self, year):
        for region in self.regions.values():
            for site in region.sites:
                site.initialize_context(self)

            first_site = region.sites[0]
            context = first_site._optimization_context
            region.optimize(year, context)

    def _consume_purchased_carrier_amounts_for_start_year(self, start_year):
        # Here we only handle the start year. The consumption of resources
        # for the following years needs to be done when applying optimization
        # results. (Also see method "_apply_results" in production_unit.)
        for region in self.regions.values():
            region.consume_purchased_carrier_amounts_for_start_year(start_year)

    def _end_simulation_after_last_year(self, year):
        if year == self._last_year:
            self.running = False

    def _finalize_visitors_if_finished(self):
        if not self.running:
            for visitor in self._visitors:
                visitor.finalize()

    def _create_time_span(self):
        options = self.options
        start_year = options['start_year']
        end_year = options['end_year']
        year_increment = options['year_increment']
        time_span = create_time_span(start_year, end_year, year_increment)
        return time_span

    def _accept_visitors(self, year):
        for visitor in self._visitors:
            for region in self.regions.values():
                region.accept(visitor, year)

    def _create_site_agents(self):
        for region in self.regions.values():
            for site in region.sites:
                agent_shape = site.geometry
                agent_creator = AgentCreator(
                    SiteAgent,
                    model=self,
                    crs=MesaSimulation.COORDINATE_REFERENCE_SYSTEM,
                    agent_kwargs={
                        'id_region': region.id,
                        'site': site,
                    },
                )
                site_agent = agent_creator.create_agent(agent_shape)
                self.grid.add_agents(site_agent)

    def _pipeline_site_relations(self):
        if not self.is_recognizing_pipelines:
            return None

        site_ids = self._site_ids()
        pipeline_indices = self.pipelines.pipeline_indices
        iterables = [site_ids, pipeline_indices]
        psr_multiindex = pd.MultiIndex.from_product(
            iterables,
            names=['site', 'pipeline'],
        )
        pipeline_site_relations = pd.DataFrame(index=psr_multiindex, columns=['distance', 'mode'])
        pipeline_site_relations = self._determine_pipeline_site_distances_in_km(pipeline_site_relations)
        return pipeline_site_relations

    def _site_ids(self):
        all_site_ids = []
        for region in self.regions.values():
            site_ids = [site.id for site in region.sites]
            all_site_ids += site_ids
        return all_site_ids

    def _determine_pipeline_site_distances_in_km(self, pipeline_site_relations):
        for region in self.regions.values():
            for site in region.sites:
                for _index, pipeline_row in self.pipelines.pipelines_df.iterrows():
                    pipeline_id = pipeline_row['id']
                    relation = pipeline_site_relations.loc[(site.id, pipeline_id)]

                    distance = self._calculate_pipeline_site_distance_in_km(site, pipeline_row)

                    relation['distance'] = distance
                    pipeline_site_relations.loc[(site.id, pipeline_id)] = relation
        return pipeline_site_relations

    def _calculate_km_distance(self, site, line):
        geometry = site.geometry
        site_coordinates = geometry.coords
        lat1 = site_coordinates[0][0]
        lon1 = site_coordinates[0][1]

        line_distance_to_closest_point_on_line = line.project(geometry)
        closest_point = line.interpolate(line_distance_to_closest_point_on_line)

        closest_point_coordinates = closest_point.coords
        lat2 = closest_point_coordinates[0][0]
        lon2 = closest_point_coordinates[0][1]
        haversine_d = self._haversine_distance_in_km(lat1, lon1, lat2, lon2)
        return haversine_d

    @staticmethod
    def _haversine_distance_in_km(lat1, lon1, lat2, lon2):
        p = pi / 180
        a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
        earth_diameter_in_km = 12742
        return earth_diameter_in_km * asin(sqrt(a))

    def _calculate_pipeline_site_distance_in_km(self, site, pipeline_row):
        line_distances = []
        line_distances_km = []
        geometry = pipeline_row['geometry']

        for line in geometry.geoms:
            fixed_line = geometry_utils.remove_duplicate_points(line, pipeline_row, self.pipelines.file_path)
            distance = site.geometry.distance(fixed_line)
            line_distances.append(distance)
            distance_km = self._calculate_km_distance(site, fixed_line)
            line_distances_km.append(distance_km)
        min_line_distance_km = min(line_distances_km)
        return min_line_distance_km

    def _update_pipelines(self):
        if self.is_recognizing_pipelines:
            self.pipelines.update_modes(self.year)
            self._update_pipeline_site_relations()

    def _update_pipeline_site_relations(self):
        for region in self.regions.values():
            for site in region.sites:
                id_site = site.id
                for _index, pipeline_row in self.pipelines.pipelines_df.iterrows():
                    id_pipeline = pipeline_row['id']
                    mode = pipeline_row['mode']

                    self.pipeline_site_relations.loc[(id_site, id_pipeline), 'mode'] = mode
