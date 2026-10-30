# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from pathlib import Path

from test_utils.isi_mock import Mock, patch

import main
from cluster import grouping_utils
from input.input_mode import InputMode
from mesa_wrapper.mesa_server import MesaServer
from region.region_factory import RegionFactory
from result.collecting_result_visitor import CollectingResultVisitor
from result.shape_file_visitor import ShapeFileVisitor
from utils import config_utils, database_utils, logging_utils


def test_main():
    simulation_options = {
        'scenario_ids': [6],
        'database_path': 'mocked_database_path',
        'input_mode': InputMode.SQLITE,
        'output_directory': 'mocked_output_directory',
    }

    with (
        patch(logging_utils.initialize_logging),
        patch(main._save_simulation_options),
        patch(config_utils.simulation_options, simulation_options),
        patch(database_utils.initialize_output_database),
        patch(main._simulate_scenario) as simulate_scenario_mock,
    ):
        try:
            main.main()
        except Exception as exception:
            message = f'main raised an exception {exception}'
            raise AssertionError(message) from exception

        # _simulate_scenario should be called with the scenario id and the unmodified simulation_options
        simulate_scenario_mock.assert_called_once_with(6, simulation_options)


def test_main_runs_multiple_scenarios():
    simulation_options = {
        'scenario_ids': [1, 2, 3],
        'database_path': 'mocked_database_path',
        'input_mode': InputMode.SQLITE,
        'output_directory': 'mocked_output_directory',
    }

    with (
        patch(logging_utils.initialize_logging),
        patch(main._save_simulation_options),
        patch(config_utils.simulation_options, simulation_options),
        patch(database_utils.initialize_output_database) as initialize_output_database_mock,
        patch(main._simulate_scenario) as simulate_scenario_mock,
    ):
        main.main()

        assert initialize_output_database_mock.call_count == 1
        assert simulate_scenario_mock.call_count == 3
        # _simulate_scenario should be called with the scenario id for each scenario
        assert [call.args[0] for call in simulate_scenario_mock.call_args_list] == [1, 2, 3]


def test_main_imports_csv_before_simulation(monkeypatch):
    simulation_options = {
        'scenario_ids': [6],
        'database_path': 'mocked_database_path',
        'input_mode': InputMode.CSV,
        'csv_input_directory': 'mocked_csv_directory',
        'output_directory': 'mocked_output_directory',
    }
    csv_to_sqlite_mock = Mock()
    monkeypatch.setattr(main, 'csv_to_sqlite', csv_to_sqlite_mock)

    with (
        patch(logging_utils.initialize_logging),
        patch(main._save_simulation_options),
        patch(config_utils.simulation_options, simulation_options),
        patch(database_utils.initialize_output_database),
        patch(main._simulate_scenario) as simulate_scenario_mock,
    ):
        main.main()

        csv_to_sqlite_mock.assert_called_once_with('mocked_csv_directory', 'mocked_database_path')
        # _simulate_scenario should be called with the scenario id and the unmodified simulation_options
        simulate_scenario_mock.assert_called_once_with(6, simulation_options)


def test_save_simulation_options_copies_toml_file(tmp_path):
    output_directory = tmp_path / 'output'

    main._save_simulation_options({'output_directory': str(output_directory)})

    copied_file = output_directory / 'simulation_options.toml'
    source_file = Path(main.__file__).parent / 'simulation_options.toml'
    assert copied_file.exists()
    assert copied_file.read_text(encoding='utf-8') == source_file.read_text(encoding='utf-8')


def mesa_server_init_mock(
    self,
    _regions,
    _simulation_options,
    _visitors,
):
    self.run = Mock()


def region_factory_init_mock(
    self,
    _id_scenario,
    _scenario_options,
):
    self.create_regions = Mock()


@patch(RegionFactory.__init__, region_factory_init_mock)
@patch(grouping_utils.assign_groups_after_load)
@patch(CollectingResultVisitor.__init__, None)
@patch(ShapeFileVisitor.__init__, None)
@patch(MesaServer.__init__, mesa_server_init_mock)
def test_simulate_scenario(monkeypatch):
    simulation_options = {'output_directory': 'mocked_output_directory'}
    export_mock = Mock()
    monkeypatch.setattr(main, 'export_product_route_shares', export_mock)

    try:
        main._simulate_scenario(1, simulation_options)
    except Exception as exception:
        message = f'simulation raised an exception {exception}'
        raise AssertionError(message) from exception

    # _simulate_scenario should export its scenario's results after running
    export_mock.assert_called_once_with(1, simulation_options)
