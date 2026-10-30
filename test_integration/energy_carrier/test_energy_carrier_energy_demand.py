# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import fixture


@fixture
def sut(energy_carrier_energy_demand):
    return energy_carrier_energy_demand


@fixture
def year():
    return 2000


def test_construction(sut):
    assert sut is not None


def test_energy_carrier(sut):
    result = sut.carrier
    assert result is not None


def test_direct_emission_in_t_co2_per_process_count(sut, year):
    result = sut.direct_emission_in_t_co2_per_process_count(year)
    assert result == 0


def test_demand_in_gj(sut, year):
    result = sut.demand_in_gj(year, 10)
    assert result == 2000  # 10 * 200


def test_purchase_cost_in_euro_per_process_count(sut, year):
    result = sut.purchase_cost_in_euro_per_process_count(year)
    # raw 200 * 42 = 8400
    assert result == 8400


def test_direct_emission_in_t_co2(sut, year):
    result = sut.direct_emission_in_t_co2(year, 10)
    assert result == 0


def test_opportunity_cost_in_euro_per_process_count(sut, year, co2_price_in_euro_per_t_co2):
    result = sut.opportunity_cost_in_euro_per_process_count(year, co2_price_in_euro_per_t_co2)
    assert result == 8000  # 200 * 40


def test_direct_emission_cost_in_euro_per_process_count(sut, year):
    result = sut.direct_emission_cost_in_euro_per_process_count(year, 0)
    assert result == 0


def test_subsidies_in_euro_per_process_count(sut, year, simulation_options):
    result = sut.subsidies_in_euro_per_process_count(year, simulation_options)
    assert result == 400  # 200 * 2


def test_taxes_in_euro_per_process_count(sut, year, simulation_options):
    result = sut.taxes_in_euro_per_process_count(year, simulation_options)
    assert result == 1200  # 200 * 6
