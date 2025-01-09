# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from energy_carrier.energy_carrier import EnergyCarrier


@pytest.fixture
def sut():
    id_energy_carrier = 0
    name = 'dummy'
    cost_2015_in_euro_per_gj = 2
    cost_2030_in_euro_per_gj = 5
    cost_2050_in_euro_per_gj = 20
    emission_2015_in_ton_per_gj = 5
    emission_2050_in_ton_per_gj = 50
    availability_2015_in_gj = 7
    availability_2050_in_gj = 70
    subsidies_2015_in_euro_per_gj = 9
    subsidies_2030_in_euro_per_gj = 39
    subsidies_2050_in_euro_per_gj = 90
    taxes_2015_in_euro_per_gj = 11
    taxes_2050_in_euro_per_gj = 110

    energy_carrier = EnergyCarrier(
        id_energy_carrier,
        name,
        cost_2015_in_euro_per_gj,
        cost_2030_in_euro_per_gj,
        cost_2050_in_euro_per_gj,
        emission_2015_in_ton_per_gj,
        emission_2050_in_ton_per_gj,
        availability_2015_in_gj,
        availability_2050_in_gj,
        subsidies_2015_in_euro_per_gj,
        subsidies_2030_in_euro_per_gj,
        subsidies_2050_in_euro_per_gj,
        taxes_2015_in_euro_per_gj,
        taxes_2050_in_euro_per_gj,
    )
    return energy_carrier


def test_cost_in_euro_per_gj(sut):
    year = 2022
    result = sut.cost_in_euro_per_gj(year)
    assert result == 2


def test_emission_in_ton_per_gj(sut):
    year = 2015
    result = sut.emission_in_ton_per_gj(year)
    assert result == 5


def test_availability_in_gj(sut):
    year = 2015
    result = sut.availability_in_gj(year)
    assert result == 7


def test_subsidies_in_euro_per_gj(sut):
    year = 2022
    result = sut.subsidies_in_euro_per_gj(year)
    assert result == 9


def test_taxes_in_euro_per_gj(sut):
    year = 2015
    result = sut.taxes_in_euro_per_gj(year)
    assert result == 11
