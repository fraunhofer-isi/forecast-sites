# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from entity import Entity
from utils import collection_utils


# pylint: disable=too-many-instance-attributes
class ProductionUnit(Entity):

    # pylint: disable=too-many-arguments
    def __init__(self, id_production_unit, product, process, production_in_tons, year_of_last_reinvestment):
        self.id = id_production_unit
        self.process = process
        self.previous_process = process
        self.production_in_tons = production_in_tons
        self.year_of_last_reinvestment = year_of_last_reinvestment
        self.previous_year_of_last_reinvestment = year_of_last_reinvestment
        self.energy_demands = process.energy_demands
        self._product = product
        # pylint: disable=fixme
        self._children = []

    def optimize_process(
        self,
        year,
        co2_cost_in_euro_per_ton_co2,
        pipeline_cost_scaling,
        distance_to_closest_h2_pipeline,
        probability_limit,
    ):
        if self.has_children:
            self._optimize_process_with_children(
                year,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
                distance_to_closest_h2_pipeline,
                self._children,
            )
        else:
            probability_of_change = self.probability_of_change(
                year,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
            )
            if probability_of_change < probability_limit:
                self._check_fuel_switch(year, co2_cost_in_euro_per_ton_co2, distance_to_closest_h2_pipeline)
                return

            available_processes = []
            for process in self._product.available_processes:
                available_processes.append(process)
                if self.check_energy_availability(year, process):
                    if self.check_h2_distance(process, distance_to_closest_h2_pipeline):
                        available_processes.remove(process)
                else:
                    available_processes.remove(process)

            self.previous_process = self.process
            self.process = self._process_with_min_production_cost(
                year,
                self.process,
                self.production_in_tons,
                available_processes,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
            )
            self.previous_year_of_last_reinvestment = self.year_of_last_reinvestment
            self.year_of_last_reinvestment = year

    def probability_of_change(
        self,
        year,
        co2_cost_in_euro_per_ton_co2,
        pipeline_cost_scaling,
    ):
        if self.has_children:
            probability = self._probability_of_change_of_children(
                year,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
                self._children,
            )
            return probability

        wait = self._check_production_cost_minima(year, co2_cost_in_euro_per_ton_co2, pipeline_cost_scaling)
        if self.year_of_last_reinvestment is not None:
            end_of_life = self.process.year_of_new_investment(self.year_of_last_reinvestment)
            if year == end_of_life + 0:
                return 1
            if end_of_life - 0 <= year < end_of_life + 0:
                if wait:
                    return 0
                return 1
            return 0
        return 1

    @staticmethod
    def check_h2_use(process):
        hydrogen = 15
        for energy_demand in process.energy_demands:
            energy_carrier = energy_demand.energy_carrier
            if energy_carrier.id == hydrogen:
                return True
        for steam_demand in process.steam_demands:
            energy_carrier = steam_demand.energy_carrier
            if energy_carrier.id == hydrogen:
                return True
        for feedstock_demand in process.feedstock_demands:
            energy_carrier = feedstock_demand.energy_carrier
            if energy_carrier.id == hydrogen:
                return True
        return False

    @property
    def has_children(self):
        return len(self._children) > 0

    def _check_fuel_switch(self, year, co2_cost_in_euro_per_ton_co2, distance_to_closest_h2_pipeline):
        direct_reduction_h2 = 38
        direct_reduction_ng = 39
        process_id = self.process.id
        if process_id in (direct_reduction_h2, direct_reduction_ng):
            available_processes = []
            for process in self._product.available_processes:
                available_processes.append(process)
                if self.check_energy_availability(year, process):
                    if self.check_h2_distance(process, distance_to_closest_h2_pipeline):
                        available_processes.remove(process)
                else:
                    available_processes.remove(process)

            self.previous_process = self.process
            self.process = self._process_with_min_energy_cost(
                year,
                self.process,
                available_processes,
                co2_cost_in_euro_per_ton_co2,
            )

    def _check_production_cost_minima(self, year, co2_cost_in_euro_per_ton_co2, pipeline_cost_scaling):
        self.previous_process = self.process
        available_processes = []
        for process in self._product.available_processes:
            available_processes.append(process)
            if not self.check_energy_availability(year, process):
                available_processes.remove(process)
        if len(available_processes) == 0:
            return None
        process_production_cost_with_pipelines = dict.fromkeys([process.id for process in available_processes])
        process_production_cost_without_pipelines = dict.fromkeys([process.id for process in available_processes])
        for process in available_processes:
            production_cost_with_pipelines = process.production_cost_in_euro(
                year,
                self.production_in_tons,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
            )
            process_production_cost_with_pipelines[process.id] = production_cost_with_pipelines
            production_cost_without_pipelines = process.production_cost_in_euro(
                year,
                self.production_in_tons,
                co2_cost_in_euro_per_ton_co2,
                1,
            )
            process_production_cost_without_pipelines[process.id] = production_cost_without_pipelines

        p_min_cost_with_pipelines = min(
            process_production_cost_with_pipelines,
            key=process_production_cost_with_pipelines.get,
        )
        p_min_cost_without_pipelines = min(
            process_production_cost_without_pipelines,
            key=process_production_cost_without_pipelines.get,
        )
        wait = False
        if p_min_cost_with_pipelines != p_min_cost_without_pipelines:
            wait = True
        return wait

    @staticmethod
    def _process_with_min_production_cost(
        year,
        default_process,
        production_in_tons,
        available_processes,
        co2_cost_in_euro_per_ton_co2,
        pipeline_cost_scaling,
    ):
        if len(available_processes) == 0:
            return default_process
        found_process = collection_utils.min_object(
            available_processes,
            lambda process: process.production_cost_in_euro(
                year,
                production_in_tons,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
            ),
            default_process,
        )
        return found_process

    @staticmethod
    def _process_with_min_energy_cost(
        year,
        default_process,
        available_processes,
        co2_cost_in_euro_per_ton_co2,
    ):
        if len(available_processes) == 0:
            return default_process
        found_process = collection_utils.min_object(
            available_processes,
            lambda process: process.energy_and_emission_cost(year, co2_cost_in_euro_per_ton_co2),
            default_process,
        )
        return found_process

    def number_of_process_usages(self, process):
        if self.process is process:
            return 1
        return 0

    def new_investment_in_euro(self, year):
        if year == self.year_of_last_reinvestment:
            investment = self.process.investment_in_euro(year, self.production_in_tons)
        else:
            investment = 0
        return investment

    def check_energy_availability(self, year, process):
        for energy_demand in process.energy_demands:
            energy_carrier = energy_demand.energy_carrier
            availability = energy_carrier.availability_in_gj(year)
            demand = energy_demand.demand_in_gj_per_ton

            for feedstock_demand in process.feedstock_demands:
                if energy_carrier == feedstock_demand.energy_carrier:
                    demand += feedstock_demand.feedstock_demand_in_gj_per_ton

            for steam_demand in process.steam_demands:
                if energy_carrier == steam_demand.energy_carrier:
                    demand += steam_demand.steam_demand_in_gj_per_ton

            total_demand = demand * self.production_in_tons

            if availability <= total_demand:
                return False

        return True

    def check_h2_distance(self, process, distance_to_closest_h2_pipeline):
        distance_threshold = 50
        if self.check_h2_use(process):
            if distance_to_closest_h2_pipeline is not None:
                distance_is_larger = distance_to_closest_h2_pipeline > distance_threshold
                return distance_is_larger
            return True
        return False

    def accept(self, visitor, year):
        visitor.visit_production_unit(self, year)
        self._product.accept(visitor, year)
        self.process.accept(visitor, year)

        for sub_production_unit in self._children:
            sub_production_unit.accept(visitor, year)

    @staticmethod
    def _optimize_process_with_children(
        year,
        co2_cost_in_euro_per_ton_co2,
        pipeline_cost_scaling,
        distance_to_closest_h2_pipeline,
        children,
    ):
        for child in children:
            child.optimize_process(
                year,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
                distance_to_closest_h2_pipeline,
            )

    @staticmethod
    def _probability_of_change_of_children(
        year,
        co2_cost_in_euro_per_ton_co2,
        pipeline_cost_scaling,
        children,
    ):
        for child in children:
            probability = child.probability_of_change(
                year,
                co2_cost_in_euro_per_ton_co2,
                pipeline_cost_scaling,
            )
            if probability:
                return 1
        return 0
