# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from data_interface import DataInterface
from mesa_wrapper.mesa_server import MesaServer
from region.region import Region
from simulation.simulation import Simulation
from simulation.simulation_mode import SimulationMode
from utils.logging_utils import initialize_logging
from utils.time_utils import create_time_span
from visitor.shape_file_visitor import ShapeFileVisitor
from visitor.tabular_result_visitor import TabularResultVisitor


def main():
    initialize_logging()
    id_scenario = 6

    scenario_options = {
        'co2_cost_2015_in_euro_per_ton_co2': 80,
        'co2_cost_2050_in_euro_per_ton_co2': 300,
        'id_product_filter': [
            22
        ],  # 22, 32, 51],  # only sites producing those products will be considered; all sites if empty array
        'region_ids': [
            1,
            2,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            29,
            31,
            32,
        ],
        'simulation_mode': SimulationMode.DETERMINISTIC,
        'is_using_mesa': True,
    }

    start_year = 2022
    end_year = 2050
    year_increment = 1
    time_span = create_time_span(start_year, end_year, year_increment)  # for example [2015]

    simulate(id_scenario, time_span, scenario_options)


def simulate(id_scenario, time_span, scenario_options):
    regions = {}
    for region_id in scenario_options['region_ids']:
        data_interface = DataInterface(id_scenario, scenario_options, region_id)
        region = Region(region_id, data_interface)
        regions[region_id] = region
    visitors = [TabularResultVisitor(), ShapeFileVisitor()]

    simulation_mode = scenario_options['simulation_mode']
    if scenario_options['is_using_mesa']:
        mesa_server = MesaServer(simulation_mode, time_span, regions, visitors)
        mesa_server.run()
    else:
        simulation = Simulation(simulation_mode, time_span, regions, visitors)
        simulation.run()


if __name__ == '__main__':
    main()
