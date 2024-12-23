# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from random import randint

from entity import Entity
from simulation.simulation_mode import SimulationMode


class Site(Entity):

    def __init__(self, id_site, geometry, production_units):
        self.id = id_site
        self.production_units = production_units
        self.geometry = geometry

    def process_year(
        self,
        year,
        simulation_mode,
        co2_cost_in_euro_per_ton_co2,
        pipeline_cost_scaling,
        distance_to_closest_H2_pipeline,
    ):
        if distance_to_closest_H2_pipeline is not None:
            if distance_to_closest_H2_pipeline < 50:
                pipeline_cost_scaling = 1
        for production_unit in self.production_units:
            if simulation_mode == SimulationMode.MONTE_CARLO:
                probability_limit = randint(0, 1)
                production_unit.optimize_process(
                    year,
                    co2_cost_in_euro_per_ton_co2,
                    pipeline_cost_scaling,
                    distance_to_closest_H2_pipeline,
                    probability_limit,
                )
            elif simulation_mode == SimulationMode.DETERMINISTIC:
                probability_limit = 1
                production_unit.optimize_process(
                    year,
                    co2_cost_in_euro_per_ton_co2,
                    pipeline_cost_scaling,
                    distance_to_closest_H2_pipeline,
                    probability_limit,
                )
            else:
                raise ValueError("Unknown simulation mode")

    def accept(self, visitor, year):
        visitor.visit_site(self, year)
        for production_unit in self.production_units:
            production_unit.accept(visitor, year)

    def number_of_process_usages(self, process):
        number_of_usages = 0
        for production_units in self.production_units:
            number_of_usages += production_units.number_of_process_usages(process)
        return number_of_usages

    @property
    def process_ids(self):
        return list(map(lambda production_unit: production_unit.process.id, self.production_units))
