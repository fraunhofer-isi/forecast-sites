# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import random
from math import asin, cos, pi, sqrt

import pandas as pd
from mesa import Model
from mesa.datacollection import DataCollector
from mesa_geo import AgentCreator, GeoSpace

from mesa_wrapper.site_agent import SiteAgent
from mesa_wrapper.time_schedule import TimeSchedule
from pipelines.pipelines import Pipelines
from simulation.simulation import Simulation


class MesaSimulation(Simulation, Model):
    COORDINATE_REFERENCE_SYSTEM = 'epsg:4326'

    def __init__(
        self,
        simulation_mode,
        time_span,
        regions,
        visitors,
    ):
        Simulation.__init__(
            self,
            simulation_mode,
            time_span,
            regions,
            visitors,
        )
        Model.__init__(self)

        # do not rename following model properties; they are required by mesa server
        self.random = random.Random()
        self.schedule = TimeSchedule(self, time_span)
        self.grid = GeoSpace(MesaSimulation.COORDINATE_REFERENCE_SYSTEM)
        self.datacollector = self._create_data_collector()
        self.running = True

        self._create_site_agents()

        self.recognize_pipelines = True
        self.pipelines = Pipelines()
        if self.recognize_pipelines:
            site_ids = self._site_ids()

            psr_multiindex = pd.MultiIndex.from_product(
                [site_ids, self.pipelines.pipeline_indices],
                names=['site', 'pipeline'],
            )
            self.pipeline_site_relations = pd.DataFrame(index=psr_multiindex, columns=['distance', 'mode'])
            self.calculate_pipeline_site_distances()

    def step(self):
        self.schedule.step()
        if self.recognize_pipelines:
            self.update_pipelines()

        self.datacollector.collect(self)
        for visitor in self._visitors:
            year = self.schedule.previous_time
            for region in self.regions.values():
                region.accept(visitor, year)

        if not self.running:
            for visitor in self._visitors:
                visitor.finalize()

    @property
    def year(self):
        return self.schedule.time

    def run(self):
        for _ in self._time_span:
            self.step()

    def _create_site_agents(self):
        for region in self.regions.values():
            for site in region.sites:
                agent_shape = site.geometry
                agent_creator = AgentCreator(
                    SiteAgent,
                    model=self,
                    crs=MesaSimulation.COORDINATE_REFERENCE_SYSTEM,
                    agent_kwargs={
                        'region_id': region.id,
                        'site': site,
                    },
                )
                site_agent = agent_creator.create_agent(agent_shape)

                self.schedule.add(site_agent)
                self.grid.add_agents(site_agent)

    def _create_data_collector(self):
        return DataCollector(
            # only model_reporters can be displayed by ChartModule of mesa server
            model_reporters={'agent_count': lambda m: m.schedule.get_agent_count()},
            agent_reporters={'process_ids': self._determine_process_ids},
        )

    def _site_ids(self):
        all_site_ids = []
        for region in self.regions.values():
            site_ids = [site.id for site in region.sites]
            all_site_ids += site_ids
        return all_site_ids

    @staticmethod
    def _determine_process_ids(site_agent):
        return site_agent.site.process_ids

    def calculate_pipeline_site_distances(self):
        for region in self.regions.values():
            for site in region.sites:
                for pipeline in self.pipelines.pipelines_df.iterrows():
                    pipeline_id = pipeline[1]['id']
                    relation = self.pipeline_site_relations.loc[(site.id, pipeline_id)]

                    distance = self.calculate_pipeline_site_distance(site, pipeline)

                    relation['distance'] = distance
                    self.pipeline_site_relations.loc[(site.id, pipeline_id)] = relation

    def calculate_km_distance(self, site, line):
        p = site.geometry

        np = line.interpolate(line.project(p))

        p_coord = p.coords
        lat1 = p_coord[0][0]
        lon1 = p_coord[0][1]

        np_coord = np.coords
        lat2 = np_coord[0][0]
        lon2 = np_coord[0][1]
        haversine_d = self.haversine_distance(lat1, lon1, lat2, lon2)
        return haversine_d

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        p = pi / 180
        a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
        return 12742 * asin(sqrt(a))

    def calculate_pipeline_site_distance(self, site, pipeline):
        line_distances = []
        line_distances_km = []
        geometry = pipeline[1]['geometry']

        for line in geometry.geoms:
            distance = site.geometry.distance(line)
            line_distances.append(distance)
            distance_km = self.calculate_km_distance(site, line)
            line_distances_km.append(distance_km)
        min_line_distance_km = min(line_distances_km)
        return min_line_distance_km

    def update_pipelines(self):
        self.pipelines.update_mode(self.schedule.time)
        self.update_pipeline_site_relations()

    def update_pipeline_site_relations(self):
        for region in self.regions.values():
            for site in region.sites:
                for pipeline in self.pipelines.pipelines_df.iterrows():
                    pipeline_id = pipeline[1]['id']
                    relation = self.pipeline_site_relations.loc[site.id, pipeline_id]
                    relation['mode'] = pipeline[1]['mode']
                    self.pipeline_site_relations.loc[site.id, pipeline_id] = relation

    def _pipeline_check(self):
        pass
