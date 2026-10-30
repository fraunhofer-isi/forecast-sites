# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import Mock, fixture, patch

from interpolation.interpolation_data import InterpolationData
from product.product_feedstock_demand import ProductFeedstockDemand


@fixture
def sut():
    # Provide zero efficiency improvement so raw demand remains unchanged across years
    efficiency_improvement_interpolation_data = InterpolationData(0, 0)
    simulation_options = {
        'start_year': 2000,
        'interim_year': 2025,
        'end_year': 2050,
    }
    product = 'mocked_product'
    sut = ProductFeedstockDemand(
        product,
        100,
        efficiency_improvement_interpolation_data,
        simulation_options,
    )
    return sut


@fixture
def year():
    return 2023


def test_product(sut):
    result = sut.product
    assert result == 'mocked_product'


def test_demand_in_t(sut, year):
    result = sut.demand_in_t(year, 5)
    # 100 raw demand * efficiency factor (1) * 5 process executions
    assert result == 500


@patch(ProductFeedstockDemand._raw_purchase_cost_in_euro_per_process_count, 20)
def test_purchase_cost_in_euro_per_process_count(sut, year):
    assert sut.purchase_cost_in_euro_per_process_count(year) == 20


def test_raw_purchase_cost_in_euro_per_process_count(sut, year):
    sut.carrier = Mock()
    sut.carrier.purchase_price_in_euro_per_t = Mock(10)
    result = sut._raw_purchase_cost_in_euro_per_process_count(year)
    # 100 demand per process count * 10 purchase price
    assert result == 1000


def test_opportunity_cost_in_euro_per_process_count(sut, year):
    sut.carrier = Mock()
    sut.carrier.sell_price_in_euro_per_t = Mock(10)
    sut.carrier.downstream_emission_in_t_co2_per_unit = Mock(return_value=0)
    result = sut.opportunity_cost_in_euro_per_process_count(year, 0)
    # 100 demand per process count * 10 sell price
    assert result == 1000


def test_subsidies_in_euro_per_process_count(sut, year):
    result = sut.subsidies_in_euro_per_process_count(year, {})
    assert result == 0


def test_taxes_in_euro_per_process_count(sut, year):
    result = sut.taxes_in_euro_per_process_count(year, {})
    assert result == 0
