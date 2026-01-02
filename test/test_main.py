# © 2024-2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from mock import Mock, patch

import main
from mesa_wrapper.mesa_server import MesaServer
from region.region_factory import RegionFactory
from simulation.simulation import Simulation
from utils import time_utils


def simulation_init_mock(
    self,
    _simulation_mode,
    _time_span,
    _co2_cost,
    _region,
):
    self.run = Mock()


def mesa_server_init_mock(
    self,
    _simulation_mode,
    _time_span,
    _co2_cost,
    _region,
):
    self.run = Mock()


def region_factory_init_mock(
    self,
    _id_scenario,
    _scenario_options,
):
    self.create_regions = Mock()


@patch.object(time_utils, 'create_time_span', return_value=['Y2015'])
@patch('main.simulate', return_value=None)
def test_main(*_args):
    try:
        main.main()
    except Exception as exception:
        message = f'main raised an exception {exception}'
        raise AssertionError(message) from exception


class TestSimulate:
    @patch.object(RegionFactory, '__init__', region_factory_init_mock)
    @patch.object(Simulation, '__init__', simulation_init_mock)
    def test_without_mesa(self):
        id_scenario = 1
        time_span = []

        scenario_options = {
            'simulation_mode': 'mocked_simulation_mode',
            'is_using_mesa': False,
        }

        try:
            main.simulate(id_scenario, time_span, scenario_options)
        except Exception as exception:
            message = f'simulation raised an exception {exception}'
            raise AssertionError(message) from exception

    @patch.object(RegionFactory, '__init__', region_factory_init_mock)
    @patch.object(MesaServer, '__init__', mesa_server_init_mock)
    def test_with_mesa(self):
        id_scenario = 1
        time_span = []

        scenario_options = {
            'simulation_mode': 'mocked_simulation_mode',
            'is_using_mesa': True,
        }

        try:
            main.simulate(id_scenario, time_span, scenario_options)
        except Exception as exception:
            message = f'simulation raised an exception {exception}'
            raise AssertionError(message) from exception
