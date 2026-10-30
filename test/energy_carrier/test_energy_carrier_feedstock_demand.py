# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import Mock, fixture, patch

from energy_carrier.energy_carrier_feedstock_demand import EnergyCarrierFeedstockDemand
from interpolation.interpolation_data import InterpolationData


@fixture
def sut():
    energy_carrier = Mock()
    energy_carrier.purchase_price_in_euro_per_gj = Mock(4)
    energy_carrier.sell_price_in_euro_per_gj = Mock(6)
    energy_carrier.upstream_emission_in_t_co2_per_gj = Mock(0.08)
    energy_carrier.downstream_emission_in_t_co2_per_unit = Mock(0.0)
    energy_carrier.renewably_bound_co2_emission_in_t_co2_per_unit = Mock(0.0)
    energy_carrier.subsidies_in_euro_per_gj = Mock(2.0)
    energy_carrier.taxes_in_euro_per_gj = Mock(0.5)

    efficiency_improvement_interpolation_data = InterpolationData(0, 0)
    simulation_options = {
        'start_year': 2000,
        'interim_year': 2025,
        'end_year': 2050,
    }

    return EnergyCarrierFeedstockDemand(
        energy_carrier,
        5,
        efficiency_improvement_interpolation_data,
        simulation_options,
    )  # 5 GJ per processes count


@fixture
def year():
    return 2030


def test_energy_carrier_property(sut):
    assert sut.energy_carrier == sut.carrier


def test_demand_in_gj(sut, year):
    # 12 * 5 = 60
    assert sut.demand_in_gj(year, 12) == 60


@patch(EnergyCarrierFeedstockDemand._raw_purchase_cost_in_euro_per_process_count, 20)
def test_purchase_cost_in_euro_per_process_count(sut, year):
    assert sut.purchase_cost_in_euro_per_process_count(year) == 20


def test_raw_purchase_cost_in_euro_per_process_count(sut, year):
    # 5 * 4 = 20
    assert sut._raw_purchase_cost_in_euro_per_process_count(year) == 20


def test_opportunity_cost_in_euro_per_process_count(sut, year):
    # 5 * 6 = 30 (with downstream and renewably bound both 0)
    assert sut.opportunity_cost_in_euro_per_process_count(year, 100) == 30


def test_purchase_cost_in_euro_total(sut, year):
    # per process 20 * executions 11 = 220
    assert sut.purchase_cost_in_euro(year, 11) == 220


def test_subsidies_in_euro_per_process_count(sut, year):
    # 5 * 2.0 = 10
    assert sut.subsidies_in_euro_per_process_count(year, 'opts') == 10


def test_taxes_in_euro_per_process_count(sut, year):
    # 5 * 0.5 = 2.5
    assert sut.taxes_in_euro_per_process_count(year, 'opts') == 2.5
