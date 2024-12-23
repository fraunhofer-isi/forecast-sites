# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from mock import MagicMock, patch

import main
from data_interface import DataInterface
from mesa_wrapper.mesa_server import MesaServer
from region.region import Region
from simulation.simulation import Simulation
from utils import time_utils


def data_interface_init_mock(self, scenario_id, region_id, time_span):
    pass


def region_init_mock(self, region_id, data_interface):
    self.id = None
    self._sites = [MagicMock(), MagicMock]
    self.accept = MagicMock()


def simulation_init_mock(self, simulation_mode, time_span, co2_cost, region):
    self.run = MagicMock()


def mesa_server_init_mock(self, simulation_mode, time_span, co2_cost, region):
    self.run = MagicMock()


@patch.object(time_utils, 'create_time_span', return_value=['Y2015'])
@patch('main.simulate', return_value=None)
def test_main(self, patched_simulate):
    try:
        main.main()
    except Exception as exc:
        assert False, f"main raised an exception {exc}"


class TestSimulate:

    @patch.object(DataInterface, '__init__', data_interface_init_mock)
    @patch.object(Region, '__init__', region_init_mock)
    @patch.object(Simulation, '__init__', simulation_init_mock)
    def test_without_mesa(self):
        id_scenario = 1
        id_region = 9
        time_span = []

        scenario_options = {'simulation_mode': 'mocked_simulation_mode', 'is_using_mesa': False}

        try:
            main.simulate(id_scenario, id_region, time_span, scenario_options)
        except Exception as exc:
            assert False, f"simulation raised an exception {exc}"

    @patch.object(DataInterface, '__init__', data_interface_init_mock)
    @patch.object(Region, '__init__', region_init_mock)
    @patch.object(MesaServer, '__init__', mesa_server_init_mock)
    def test_with_mesa(self):
        id_scenario = 1
        id_region = 9
        time_span = []

        scenario_options = {'simulation_mode': 'mocked_simulation_mode', 'is_using_mesa': True}

        try:
            main.simulate(id_scenario, id_region, time_span, scenario_options)
        except Exception as exc:
            assert False, f"simulation raised an exception {exc}"
