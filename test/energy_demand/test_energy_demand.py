# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import Mock

import pytest

from energy_demand.energy_demand import EnergyDemand


@pytest.fixture
def sut():
    energy_carrier = Mock()
    energy_carrier.cost_in_euro_per_gj.return_value = 1
    energy_carrier.emission_in_ton_per_gj.return_value = 2
    energy_carrier.subsidies_in_euro_per_gj.return_value = 3
    energy_carrier.taxes_in_euro_per_gj.return_value = 4
    energy_carrier.id.return_value = 5
    energy_carrier.id = 5
    demand_in_gj_per_ton = 10
    energy_demand = EnergyDemand(energy_carrier, demand_in_gj_per_ton)
    return energy_demand


def test_energy_carrier_cost_in_euro_per_ton(sut):
    year = 2015
    result = sut.energy_carrier_cost_in_euro_per_ton(year)
    assert result == 10


def test_energy_carrier_emission_in_ton_co2_per_ton(sut):
    year = 2015
    result = sut.energy_carrier_emission_in_ton_co2_per_ton(year)
    assert result == 20


def test_energy_carrier_subsidies_in_euro_per_ton(sut):
    year = 2015
    result = sut.energy_carrier_subsidies_in_euro_per_ton(year)
    assert result == 30


def test_energy_carrier_taxes_in_euro_per_ton(sut):
    year = 2015
    result = sut.energy_carrier_taxes_in_euro_per_ton(year)
    assert result == 40


def test_get_energy_carrier_id(sut):
    result = sut.get_energy_carrier_id()
    assert result == 5
