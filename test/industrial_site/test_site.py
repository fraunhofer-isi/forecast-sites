# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import random
from unittest.mock import Mock

import pytest

from industrial_site.site import Site
from simulation.simulation_mode import SimulationMode


@pytest.fixture
def sut():
    site_id = 1
    geometry = Mock()
    production_units = [Mock(), Mock(), Mock()]
    index = 1
    for production_unit in production_units:
        process = Mock()
        process.id = index
        production_unit.process = process
        production_unit.probability_of_change.return_value = 1
        production_unit.number_of_process_usages.return_value = 1
        index += 1

    site = Site(
        site_id,
        geometry,
        production_units,
    )
    return site


class TestProcessYear:
    def test_deterministic_mode(self, sut):
        sut.process_year(2018, SimulationMode.DETERMINISTIC, 0, 1, 1)
        for product in sut.production_units:
            assert product.optimize_process.called is True

    def test_monte_carlo_mode(self, sut):
        random.seed(74868)
        sut.process_year(2017, SimulationMode.MONTE_CARLO, 0, 1, 1)
        for product in sut.production_units:
            assert product.optimize_process.called is True

    def test_unknown_mode(self, sut):
        with pytest.raises(ValueError, match='Unknown simulation mode'):
            sut.process_year(2015, 'FakeMode', 0, 1, 1)


def test_visitor_call(sut):
    visitor = Mock()
    year = 2015
    sut.accept(visitor, year)
    assert visitor.visit_site.called

    for product in sut.production_units:
        assert product.accept.called is True


def test_number_of_process_usage(sut):
    process = Mock()
    assert sut.number_of_process_usages(process) == 3


def test_process_ids(sut):
    process_ids = sut.process_ids
    assert process_ids == [1, 2, 3]
