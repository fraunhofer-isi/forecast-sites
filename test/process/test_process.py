# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import MagicMock, Mock

import pytest

from process.process import Process


@pytest.fixture
def sut():
    id_process = 39
    capex_2015_in_euro_per_ton = 2
    capex_2050_in_euro_per_ton = 20
    opex_2015_in_euro_per_ton = 2
    opex_2050_in_euro_per_ton = 20
    lifetime_in_years = 2
    interest_rate = 1
    depreciation_period = 1
    process_emission_in_ton_co2_per_ton = 2
    efficiency_improvement_2015 = 0
    efficiency_improvement_2050 = 0
    investment_funding_2015 = 0
    investment_funding_2050 = 0
    investment_flexibility_2015 = 0
    investment_flexibility_2050 = 0
    energy_demands = MagicMock()

    process = Process(
        id_process,
        capex_2015_in_euro_per_ton,
        capex_2050_in_euro_per_ton,
        opex_2015_in_euro_per_ton,
        opex_2050_in_euro_per_ton,
        lifetime_in_years,
        interest_rate,
        depreciation_period,
        process_emission_in_ton_co2_per_ton,
        efficiency_improvement_2015,
        efficiency_improvement_2050,
        investment_funding_2015,
        investment_funding_2050,
        investment_flexibility_2015,
        investment_flexibility_2050,
        energy_demands,
    )
    return process


def test_accept(sut):
    visitor = Mock()
    year = 2015
    sut.accept(visitor, year)
    assert visitor.visit_process.called


def test_production_cost_in_euro(sut):
    year = 2015
    production_in_tons = 10
    pipeline_cost_scaling = 1
    co2_cost_in_euro_per_ton_c02 = 2
    result = sut.production_cost_in_euro(year, production_in_tons, co2_cost_in_euro_per_ton_c02, pipeline_cost_scaling)
    assert result == 100


def test_check_energy_carrier(sut):
    sut.used_energy_carriers()
    for demand in sut.energy_demands:
        assert demand.get_energy_carrier_id.called


def test_process_emission_in_tons(sut):
    result = sut.process_emission_in_tons(production_in_tons=2)
    assert result == 4


def test_investment_in_euro(sut):
    sut._capex_in_euro_per_ton = MagicMock(return_value=10)
    sut._investment_funding = MagicMock(return_value=0)
    result = sut.investment_in_euro(year=2020, production_in_tons=2)
    assert result == 10 * 2


def test_annuity_on_investment(sut):
    sut.annuity_on_investment_per_ton = MagicMock(return_value=10)
    result = sut.annuity_on_investment(year=2020, production_in_tons=2)
    assert result == 10 * 2


def test_year_of_new_investment(sut):
    result = sut.year_of_new_investment(year_of_last_reinvestment=2020)
    assert result == 2 + 2020


def test_energy_emissions_in_ton_co2_per_ton(sut):
    result = sut.energy_emissions_in_ton_co2_per_ton(year=2015)
    assert result == 0


def test_production_cost_in_euro_per_ton(sut):
    result = sut.production_cost_in_euro_per_ton(year=2015)
    assert result == 6


def test_energy_and_emission_cost(sut):
    year = 2015
    sut.energy_carrier_cost_in_euro_per_ton = MagicMock(return_value=2)
    sut.energy_emissions_in_ton_co2_per_ton = MagicMock(return_value=1)
    co2_cost_in_euro_per_ton_c02 = 2
    result = sut.energy_and_emission_cost(year, co2_cost_in_euro_per_ton_c02)
    assert result == 4


def test_annuity_factor(sut):
    result = sut._annuity_factor()
    assert result == 2


def test_annuity_on_pipeline_investment(sut):
    pipeline_cost = 1
    result = sut._annuity_on_pipeline_investment(pipeline_cost)
    return result == 2


def test_annuity_on_investment_per_ton(sut):
    year = 2015
    result = sut.annuity_on_investment_per_ton(year)
    assert result == 4


def test_energy_carrier_cost_in_euro_per_ton(sut):
    result = sut.energy_carrier_cost_in_euro_per_ton(year=2015)
    assert result == 0


def test_energy_carrier_subsidies_in_euro_per_ton(sut):
    result = sut._energy_carrier_subsidies_in_euro_per_ton(year=2015)
    assert result == 0


def test_energy_carrier_taxes_in_euro_per_ton(sut):
    result = sut._energy_carrier_taxes_in_euro_per_ton(year=2015)
    assert result == 0


def test_capex_in_euro_per_ton(sut):
    year = 2015
    result = sut._capex_in_euro_per_ton(year)
    assert result == 2


def test_opex_in_euro_per_ton(sut):
    year = 2015
    result = sut.opex_in_euro_per_ton(year)
    assert result == 2


def test_efficiency_improvement(sut):
    year = 2015
    result = sut._efficiency_improvement(year)
    assert result == 0


def test_investment_funding(sut):
    year = 2015
    result = sut._investment_funding(year)
    assert result == 0


def test_investment_flexibility(sut):
    year = 2015
    result = sut._investment_flexibility(year)
    assert result == 0
