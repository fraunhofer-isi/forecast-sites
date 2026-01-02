# © 2024-2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import Mock

import pytest

from simulation.simulation import Simulation
from simulation.simulation_mode import SimulationMode


@pytest.fixture
def sut():
    simulation_mode = SimulationMode.DETERMINISTIC
    time_span = [2015, 2017]
    region = Mock()
    visitors = [Mock(return_value=None) for i in range(3)]

    simulation = Simulation(simulation_mode, time_span, region, visitors)
    simulation._export_sites = Mock(return_value=None)
    return simulation


def test_run(sut):
    sut.run()
    assert sut.region.accept.call_count == 6
    assert sut.region.process_year.call_count == 2


def test_process_year(sut):
    sut._process_year(2015)
    assert sut.region.process_year.called
