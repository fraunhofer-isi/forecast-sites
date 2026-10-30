# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import Mock, fixture, patch, patch_property

from carrier.carrier_unit import CarrierUnit
from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand
from interpolation.interpolation_data import InterpolationData
from processes.process_emission import ProcessEmission
from product.product_feedstock_demand import ProductFeedstockDemand

simulation_options = {
    'start_year': 2000,
    'end_year': 2050,
}


@fixture
def sut():
    process = Mock()
    return ProcessEmission(process)


def test_construction(sut):
    assert sut is not None


@patch(ProcessEmission._direct_emissions_of_energy_demands_in_t_co2_per_process_count, 3)
def test_direct_emissions_in_t_co2_per_process_count(sut):
    sut._process.non_energy_direct_process_emission_in_t_co2_per_process_count = 2
    year = 2020
    result = sut.direct_emissions_in_t_co2_per_process_count(year)
    assert result == 5


@patch_property(ProcessEmission.captured_input_emission_in_t_co2_per_process_count, 10)
def test_captured_emission_in_t_co2_per_process_count(sut):
    sut._process.carbon_capture_rate = 0.5
    result = sut.captured_emission_in_t_co2_per_process_count
    assert result == 5  # 10 * 0.5


class TestCapturedInputEmissionInTCo2PerProcessCount:
    def test_for_capture_process(self, sut):
        sut._process.is_capture_process = True
        result = sut.captured_input_emission_in_t_co2_per_process_count
        assert result == 1

    def test_for_normal_process(self, sut):
        sut._process.is_capture_process = False
        result = sut.captured_input_emission_in_t_co2_per_process_count
        assert result == 0


@patch(EnergyCarrierEnergyDemand.direct_emission_in_t_co2_per_process_count, 5)
def test_direct_emissions_of_energy_demands_in_t_co2_per_process_count(sut):
    interpolation = InterpolationData(0, 0)
    demand1 = EnergyCarrierEnergyDemand(Mock(), 0, interpolation, simulation_options)
    demand2 = EnergyCarrierEnergyDemand(Mock(), 0, interpolation, simulation_options)
    demand3 = ProductFeedstockDemand(Mock(), 0, interpolation, simulation_options)

    sut._process.demands = [demand1, demand2, demand3]
    year = 2020
    result = sut._direct_emissions_of_energy_demands_in_t_co2_per_process_count(year)
    assert result == 10


@patch(ProcessEmission.direct_emissions_in_t_co2_per_process_count, 5)
def test_direct_emissions_in_t_co2(sut):
    year = 2020
    result = sut.direct_emissions_in_t_co2(year, 4)
    assert result == 20


@patch_property(ProcessEmission.captured_emission_in_t_co2_per_process_count, 5)
def test_captured_emission_in_t_co2(sut):
    result = sut.captured_emission_in_t_co2(4)
    assert result == 20


@patch(ProcessEmission.direct_emissions_in_t_co2, 6)
def test_direct_emission_cost_in_euro(sut):
    year = 2020
    result = sut.direct_emission_cost_in_euro(year, 3, 4)
    assert result == 6 * 4


@patch(ProcessEmission.direct_non_energy_emission_cost_in_euro_per_process_count, 5)
@patch(ProcessEmission.direct_energy_emission_cost_in_euro_per_process_count, 7)
def test_direct_emission_cost_in_euro_per_process_count(sut):
    year = 2020
    result = sut.direct_emission_cost_in_euro_per_process_count(year, 123)
    assert result == 12


@patch_property(ProcessEmission.captured_input_emission_in_t_co2_per_process_count, 4)
def test_savings_due_to_captured_emissions_in_euro_per_process_count(sut):
    sut._process.carbon_capture_rate = 0.5
    result = sut.savings_due_to_captured_emissions_in_euro_per_process_count(10)
    assert result == 20  # 4 * 0.5 * 10


@patch(ProcessEmission._direct_emissions_of_energy_demands_in_t_co2_per_process_count, 5)
def test_direct_energy_emissions_in_t_co2(sut):
    year = 2020
    result = sut.direct_energy_emissions_in_t_co2(year, 4)
    assert result == 20


@patch(ProcessEmission.direct_energy_emissions_in_t_co2, 7)
def test_direct_energy_emission_cost_in_euro(sut):
    year = 2020
    result = sut.direct_energy_emission_cost_in_euro(year, 3, 10)
    assert result == 70


def test_direct_energy_emission_cost_in_euro_per_process_count(sut):
    demand_energy_1 = Mock()
    demand_energy_1.direct_emission_cost_in_euro_per_process_count = Mock(3)
    demand_energy_2 = Mock()
    demand_energy_2.direct_emission_cost_in_euro_per_process_count = Mock(4)
    non_energy_demand = Mock()  # Should be ignored
    sut._process.demands = [demand_energy_1, demand_energy_2, non_energy_demand]

    # Simulate EnergyCarrierEnergyDemand type check by setting class
    demand_energy_1.__class__ = EnergyCarrierEnergyDemand
    demand_energy_2.__class__ = EnergyCarrierEnergyDemand

    year = 2020
    result = sut.direct_energy_emission_cost_in_euro_per_process_count(year, 99)
    assert result == 7


def test_direct_non_energy_emissions_in_t_co2(sut):
    sut._process.non_energy_direct_process_emission_in_t_co2_per_process_count = 2
    result = sut.direct_non_energy_emissions_in_t_co2(5)
    assert result == 10


@patch(ProcessEmission.direct_non_energy_emissions_in_t_co2, 9)
def test_direct_non_energy_emission_cost_in_euro(sut):
    result = sut.direct_non_energy_emission_cost_in_euro(3, 11)
    assert result == 99


def test_direct_non_energy_emission_cost_in_euro_per_process_count(sut):
    sut._process.non_energy_direct_process_emission_in_t_co2_per_process_count = 3
    result = sut.direct_non_energy_emission_cost_in_euro_per_process_count(4)
    assert result == 12


@patch(ProcessEmission.captured_emission_in_t_co2, 10)
def test_saving_due_to_captured_emission_in_euro(sut):
    result = sut.saving_due_to_captured_emission_in_euro(4, 20)
    assert result == 200  # 10 * 20


def test_energy_carrier_production_direct_emissions_in_t_co2(sut):
    carrier_gj = Mock()
    carrier_gj.unit = CarrierUnit.GJ
    carrier_gj.direct_emission_in_t_co2_per_gj = 0.5

    carrier_t = Mock()
    carrier_t.unit = CarrierUnit.T  # Should be ignored
    sut._process.output_carriers = [carrier_gj, carrier_t]
    sut._process.production_in_gj = Mock(10)

    result = sut.energy_carrier_production_direct_emissions_in_t_co2(4)
    assert result[carrier_gj] == 5  # 10 * 0.5
    assert carrier_t not in result
    sut._process.production_in_gj.assert_called_once_with(carrier_gj, 4)


def test_emissions_in_t_co2_not_implemented(sut):
    with pytest.raises(NotImplementedError):
        sut.emissions_in_t_co2(1)
