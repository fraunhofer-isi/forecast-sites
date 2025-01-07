# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from mock import MagicMock, patch

from production_unit.production_unit import ProductionUnit


@pytest.fixture
def sut():
    id_production_unit = 1
    product = MagicMock()

    process = MagicMock()
    process.lifetime_in_years.return_value = 10

    production_in_tons = 1
    year_of_last_reinvestment = 2020

    production_unit = ProductionUnit(
        id_production_unit,
        product,
        process,
        production_in_tons,
        year_of_last_reinvestment,
    )
    return production_unit


class TestProbabilityOfChange:

    def test_without_year_of_last_reinvestment(self, sut):
        sut.year_of_last_reinvestment = None
        result = sut._probability_of_change(2020, 1, 1)
        assert result == 1

    def test_end_of_life_before_year(self, sut):
        sut.process.year_of_new_investment = MagicMock(return_value=2010)
        result = sut._probability_of_change(2020)
        assert result == 1

    def test_end_of_life_after_year(self, sut):
        sut.process.year_of_new_investment = MagicMock(return_value=2030)
        result = sut._probability_of_change(2020)
        assert result == 0


def test_check_production_cost_minima(sut):
    year = 2015
    co2_cost_in_euro_per_ton_co2 = 2
    pipeline_cost_scaling = 1
    sut._check_production_cost_minima(year, co2_cost_in_euro_per_ton_co2, pipeline_cost_scaling)
    assert sut.check_energy_availability.called


def test_check_fuel_switch(sut):
    year = 2015
    sut.process.id = 39
    co2_cost_in_euro_per_ton_co2 = 2
    distance_to_closest_h2_pipeline = 1
    sut._check_fuel_switch(year, co2_cost_in_euro_per_ton_co2, distance_to_closest_h2_pipeline)
    assert sut.check_energy_availability.called


def test_optimize_process(sut):
    process_with_min_production_cost = sut._process_with_min_production_cost
    sut._process_with_min_production_cost = MagicMock(return_value='mocked_process')
    year = 2020
    co2_cost_in_euro_per_ton_co2 = 2
    sut.optimize_process(year, co2_cost_in_euro_per_ton_co2)
    assert sut.process == 'mocked_process'
    sut._process_with_min_production_cost = process_with_min_production_cost


@patch('utils.collection_utils.min_object', return_value='mocked_min_object')
def test_process_with_min_production_cost(patched_min_object, sut):
    year = 2020
    default_process = MagicMock()
    production_in_tons = 2
    co2_cost_in_euro_per_ton_co2 = 2
    pipeline_cost_scaling = 1
    result = sut._process_with_min_production_cost(
        year,
        default_process,
        production_in_tons,
        co2_cost_in_euro_per_ton_co2,
        pipeline_cost_scaling,
    )
    patched_min_object.assert_called()
    assert result == 'mocked_min_object'


class TestProcessWithMinEnergyCost:

    @patch('utils.collection_utils.min_object', return_value='mocked_min_object')
    def test_with_available_processes(self, patched_min_object, sut):
        year = 2020
        default_process = MagicMock()
        available_processes = ['mocked_process']
        co2_cost_in_euro_per_ton_co2 = 2
        result = sut._process_with_min_energy_cost(
            year,
            default_process,
            available_processes,
            co2_cost_in_euro_per_ton_co2,
        )
        patched_min_object.assert_called()
        assert result == 'mocked_min_object'

    def test_without_available_processes(self, sut):
        year = 2020
        default_process = MagicMock()
        available_processes = []
        co2_cost_in_euro_per_ton_co2 = 2
        result = sut._process_with_min_energy_cost(
            year,
            default_process,
            available_processes,
            co2_cost_in_euro_per_ton_co2,
        )
        assert result == default_process


class TestNumberOfProcessUsages:

    def test_process_is_used(self, sut):
        process = sut.process
        result = sut.number_of_process_usages(process)
        assert result == 1

    def test_process_is_not_used(self, sut):
        process = MagicMock()
        result = sut.number_of_process_usages(process)
        assert result == 0


class TestNewInvestmentInEuro:

    def test_year_is_year_of_new_investment(self, sut):
        sut.previous_process.year_of_new_investment = MagicMock(return_value=2020)
        sut.process.investment_in_euro = MagicMock(return_value=999)
        investment = sut.new_investment_in_euro(2020)
        assert investment == 999

    def test_year_is_not_year_of_new_investment(self, sut):
        sut.previous_process.year_of_new_investment = MagicMock(return_value=2022)
        investment = sut.new_investment_in_euro(2020)
        assert investment == 0


class TestCheckEnergyAvailability:

    def test_energy_is_available(self, sut):
        year = 2015  # Set the desired year for testing
        process = MagicMock()  # Mock the process object
        energy_demand = MagicMock()  # Mock an energy_demand object
        energy_carrier = MagicMock()  # Mock an energy_carrier object
        # Set up the necessary attributes and return values of the mocked objects
        energy_demand.energy_carrier = energy_carrier
        energy_carrier.availability_in_gj.return_value = 100  # Set availability greater than demand
        energy_demand.demand_in_gj_per_ton = 10
        sut.production_in_tons = 5  # Set the production in tons for testing
        process.energy_demands = [energy_demand]  # Assign the energy_demand to the process

        # Call the method under test
        result = sut.check_energy_availability(year, process)

        # Assert the expected behavior
        assert result is True

    def test_energy_is_not_available(self, sut):
        # Set up the test case with an energy_demand that has insufficient availability
        year = 2015  # Set the desired year for testing
        process = MagicMock()  # Mock the process object
        energy_demand = MagicMock()  # Mock an energy_demand object
        energy_carrier = MagicMock()  # Mock an energy_carrier object
        # Set up the necessary attributes and return values of the mocked objects
        energy_demand.energy_carrier = energy_carrier
        energy_carrier.availability_in_gj.return_value = 10  # Set availability less than demand
        energy_demand.demand_in_gj_per_ton = 10
        sut.production_in_tons = 5  # Set the production in tons for testing
        process.energy_demands = [energy_demand]  # Assign the energy_demand to the process

        # Call the method under test
        result = sut.check_energy_availability(year, process)

        # Assert the expected behavior
        assert result is False


def test_check_h2_use(sut):
    process = MagicMock()  # Mock the process object
    energy_demand = MagicMock()  # Mock an energy_demand object
    energy_carrier = MagicMock(return_value=15)
    process.energy_demands = [energy_demand]
    energy_demand.energy_carrier = energy_carrier
    result = sut.check_h2_use(process)
    assert result is True


def test_check_h2_distance(sut):
    distance_to_closest_h2_pipeline = 20
    result = sut.check_h2_distance(distance_to_closest_h2_pipeline)
    assert result is True


def test_accept(sut):
    visitor = MagicMock()
    year = 2020

    sut._children = [MagicMock()]
    sut.accept(visitor, year)
    assert sut._product.accept.called
    assert sut.process.accept.called
    assert sut._children[0].accept.called
