# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from types import SimpleNamespace

import pytest

from by_product.by_product import ByProduct
from carrier.carrier import Carrier
from carrier.carrier_unit import CarrierUnit
from processes.abstract_process import AbstractProcess
from product.product import Product


class UnknownUnitCarrier(Carrier):
    @property
    def unit(self):
        return 'mystery'


class FakeOutput:
    def __init__(self, carrier, t_value=0.0, gj_value=0.0):
        self.carrier = carrier
        self.output_in_t_per_process_count = t_value
        self.output_in_gj_per_process_count = gj_value

    def accept(self, visitor, year):
        return visitor.output_result(self.carrier, year)


def _product_data():
    return {
        'purchase_price_in_euro_per_t': {'2026': 1.0},
        'sell_price_in_euro_per_t': {'2026': 2.0},
        'upstream_emission_start_year_in_t_co2_per_t': {'2026': 0.1},
        'upstream_emission_end_year_in_t_co2_per_t': {'2026': 0.1},
        'downstream_emission_in_t_co2_per_t': 0.0,
        'maximum_production_in_t': 10.0,
    }


def _create_process_data(demands=(), outputs=(), depreciation_period=5):
    return SimpleNamespace(
        demands=tuple(demands),
        outputs=tuple(outputs),
        carbon_capture_rate=0.0,
        sector_ids=(1,),
        lifetime_in_years=20,
        tech_available_at_year=2020,
        depreciation_period=depreciation_period,
        life_extension_factor=1.0,
        non_energy_direct_process_emission_in_t_co2_per_process_count=0.0,
        capex_interpolation_data_in_euro_per_process_count=None,
        opex_interpolation_data_in_euro_per_process_count=None,
        investment_funding_interpolation_data_in_euro_per_process_count=None,
        efficiency_improvement_interpolation_data=None,
    )


def _create_product(identifier=1):
    return Product(identifier, f'Product {identifier}', _product_data())


def _create_by_product(identifier=1):
    return ByProduct(identifier, f'ByProduct {identifier}', _product_data())


def _demand(carrier, t_value=0.0, gj_value=0.0):
    return SimpleNamespace(
        carrier=carrier,
        demand_in_t_per_process_count=lambda year: t_value + year * 0,
        demand_in_gj_per_process_count=lambda year: gj_value + year * 0,
    )


def _output(carrier, t_value=0.0, gj_value=0.0):
    return FakeOutput(carrier, t_value=t_value, gj_value=gj_value)


def test_used_and_output_carriers_preserve_order_and_remove_duplicates():
    product = _create_product(1)
    by_product = _create_by_product(2)
    process = AbstractProcess(
        1,
        _create_process_data(
            demands=[_demand(product), _demand(product), _demand(by_product)],
            outputs=[_output(by_product), _output(product), _output(by_product)],
        ),
    )

    assert process.output_carriers == [by_product, product]
    assert process.used_carriers == [product, by_product]


def test_output_product_and_by_product_lists_filter_by_type():
    product = _create_product(1)
    by_product = _create_by_product(2)
    other_carrier = SimpleNamespace(unit=CarrierUnit.GJ)
    process = AbstractProcess(1, _create_process_data(outputs=[_output(product), _output(by_product), _output(other_carrier)]))

    assert process.output_products == [product]
    assert process.output_by_products == [by_product]


def test_efficiency_related_interpolation_data_properties_delegate_to_process_data():
    process_data = _create_process_data()
    process = AbstractProcess(1, process_data)

    assert process.capex_interpolation_data_in_euro_per_process_count is None
    assert process.opex_interpolation_data_in_euro_per_process_count is None
    assert process.investment_funding_interpolation_data_in_euro_per_process_count is None
    assert process.efficiency_improvement_interpolation_data is None


def test_accept_visits_outputs_and_returns_exit_result():
    first_output = _output(_create_product(1), t_value=1.0)
    second_output = _output(_create_by_product(2), t_value=2.0)
    process = AbstractProcess(1, _create_process_data(outputs=[first_output, second_output]))
    visitor = SimpleNamespace(
        enter_process=lambda process_obj, year: ('enter', process_obj.id, year),
        exit_process=lambda process_obj, year, enter_result, child_results: (
            process_obj.id,
            year,
            enter_result,
            list(child_results.values()),
        ),
        output_result=lambda carrier, year: f'{carrier.name}-{year}',
    )

    result = process.accept(visitor, 2030)

    assert result == (1, 2030, ('enter', 1, 2030), ['Product 1-2030', 'ByProduct 2-2030'])


def test_production_helpers_select_unit_and_sum_matching_outputs():
    product = _create_product(1)
    carrier_gj = SimpleNamespace(unit=CarrierUnit.GJ)
    process = AbstractProcess(
        1,
        _create_process_data(
            outputs=[_output(product, t_value=2.5), _output(product, t_value=1.5), _output(carrier_gj, gj_value=6.0)],
        ),
    )

    assert process._production_in_unit_per_process_count(product) == 4.0
    assert process._production_in_unit_per_process_count(carrier_gj) == 6.0
    assert process.production_in_gj(carrier_gj, 3) == 18.0


def test_consumption_helpers_select_unit_and_sum_matching_demands():
    product = _create_product(1)
    carrier_gj = SimpleNamespace(unit=CarrierUnit.GJ)
    process = AbstractProcess(
        1,
        _create_process_data(
            demands=[_demand(product, t_value=2.0), _demand(product, t_value=1.0), _demand(carrier_gj, gj_value=7.0)],
        ),
    )

    assert process._consumption_in_unit_per_process_count(2026, product) == 3.0
    assert process._consumption_in_unit_per_process_count(2026, carrier_gj) == 7.0
    assert process.netto_produced_or_consumed_amount_per_process_count(2026, product) == -3.0


def test_unknown_carrier_unit_raises_for_production_and_consumption():
    carrier = UnknownUnitCarrier(9, 'Unknown')
    process = AbstractProcess(1, _create_process_data())

    with pytest.raises(TypeError, match='Unknown carrier unit'):
        process._production_in_unit_per_process_count(carrier)

    with pytest.raises(TypeError, match='Unknown carrier unit'):
        process._consumption_in_unit_per_process_count(2026, carrier)


def test_compound_factor_raises_when_depreciation_period_is_zero():
    with pytest.raises(ValueError, match='[Dd]epreciation period'):
        AbstractProcess(1, _create_process_data(depreciation_period=0))
