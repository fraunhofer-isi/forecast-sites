# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from _pytest.python_api import approx
from test_utils.isi_mock import fixture

from carrier.carrier_unit import CarrierUnit


@fixture
def sut(product):
    return product


def test_construction(sut):
    assert sut is not None


def test_unit(sut):
    result = sut.unit
    assert result == CarrierUnit.T


class TestPurchasePriceInEuroPerT:
    def test_start_year(self, sut):
        assert sut.purchase_price_in_euro_per_t(2000) == 450

    def test_year_after_last_year(self, sut):
        assert sut.purchase_price_in_euro_per_t(2060) == 500


def test_purchase_price_in_euro_per_unit(sut):
    assert sut.purchase_price_in_euro_per_unit(2000) == 450


def test_purchase_cost_in_euro(sut):
    result = sut.purchase_cost_in_euro(10, 2000)
    assert result == 4500  # 10 * 450


class TestSellPriceInEuroPerT:
    def test_start_year(self, sut):
        assert sut.sell_price_in_euro_per_t(2000) == 430

    def test_year_after_last_year(self, sut):
        assert sut.sell_price_in_euro_per_t(2060) == 480


def test_upstream_emission_in_t_co2_per_t(sut, simulation_options):
    result = sut.upstream_emission_in_t_co2_per_t(2025, simulation_options)
    assert result == approx(1.6)  # 1.5 + (1.7 - 1.5)/ 2
