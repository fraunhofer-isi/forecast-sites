# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from _pytest.python_api import approx
from test_utils.isi_mock import fixture


@fixture
def sut(energy_carrier):
    return energy_carrier


def test_construction(sut):
    assert sut is not None


class TestPurchasePrice:
    def test_start_year(self, sut):
        assert sut.purchase_price_in_euro_per_gj(2000) == 42

    def test_fallback_last_known_year(self, sut):
        assert sut.purchase_price_in_euro_per_gj(2055) == 40


class TestSellPrice:
    def test_start_year(self, sut):
        assert sut.sell_price_in_euro_per_gj(2000) == 40

    def test_fallback_last_known_year(self, sut):
        assert sut.sell_price_in_euro_per_gj(2055) == 38


def test_direct_emission(sut):
    assert sut.direct_emission_in_t_co2_per_gj == 0.0


def test_upstream_emission(sut, simulation_options):
    result = sut.upstream_emission_in_t_co2_per_gj(2025, simulation_options)
    assert result == approx(0.075)  # 0.1 + (0.05 - 0.1)/ 2


def test_upstream_emission_per_unit(sut, simulation_options):
    result = sut.upstream_emission_in_t_co2_per_unit(2025, simulation_options)
    assert result == approx(0.075)


def test_minimum_use(sut, simulation_options):
    result = sut.minimum_use_in_unit(2025, simulation_options)
    assert result == approx(0)


def test_subsidies(sut, simulation_options):
    result = sut.subsidies_in_euro_per_gj(2025, simulation_options)
    assert result == approx(1)


def test_taxes(sut, simulation_options):
    result = sut.taxes_in_euro_per_gj(2025, simulation_options)
    assert result == approx(5.5)  # 5 + (6 - 5)/2
