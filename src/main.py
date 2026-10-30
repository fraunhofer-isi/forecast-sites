# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import logging
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from cluster import grouping_utils
from input.csv_to_sqlite import csv_to_sqlite
from input.input_mode import InputMode
from mesa_wrapper.mesa_server import MesaServer
from region.region_factory import RegionFactory
from result.collecting_result_visitor import CollectingResultVisitor
from result.product_route_share_export import export_product_route_shares
from result.shape_file_visitor import ShapeFileVisitor
from utils import config_utils, database_utils, logging_utils


def main() -> None:
    logging_utils.initialize_logging()
    logging.info('Running forecast-sites by Fraunhofer ISI...')

    simulation_options = config_utils.simulation_options()
    _prepare_database_access(simulation_options)

    _save_simulation_options(simulation_options)
    database_utils.initialize_output_database(simulation_options)

    _simulate_scenarios(simulation_options)


def _simulate_scenarios(simulation_options):
    for id_scenario in simulation_options['scenario_ids']:
        _simulate_scenario(id_scenario, simulation_options)


def _prepare_database_access(simulation_options):
    database_path = simulation_options['database_path']

    if simulation_options['input_mode'] == InputMode.CSV:
        input_directory = simulation_options['csv_input_directory']

        logging.info('Importing *.csv data from "%s" to "./resources/input/input.sqlite"', input_directory)
        csv_to_sqlite(input_directory, database_path)

    logging.info('Starting model with input from %s', database_path)


def _save_simulation_options(simulation_options: Mapping[str, Any]) -> None:
    output_directory = simulation_options['output_directory']
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    # Get the source TOML file path
    source_toml = Path(__file__).parent / 'simulation_options.toml'
    destination_toml = Path(output_directory) / 'simulation_options.toml'

    # Copy the TOML file to the output directory
    shutil.copy2(source_toml, destination_toml)

    logging.info('Simulation options copied to %s', destination_toml)


def _simulate_scenario(
    id_scenario: int,
    simulation_options: Mapping[str, Any],
) -> None:
    region_factory = RegionFactory(id_scenario, simulation_options)
    regions = region_factory.create_regions()

    grouping_utils.assign_groups_after_load(regions, simulation_options)

    visitors = [
        CollectingResultVisitor(simulation_options),
        ShapeFileVisitor(simulation_options),
    ]

    mesa_server = MesaServer(
        regions,
        simulation_options,
        visitors,
    )
    mesa_server.run()  # Also see MesaSimulation.step() for the main simulation steps
    export_product_route_shares(id_scenario, simulation_options)


if __name__ == '__main__':
    main()  # pragma: no cover
