# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import fixture


@fixture
def sut(production_unit):
    return production_unit


def test_construction(sut):
    assert sut is not None


def test_available_process_options(sut):
    pass  # TODO #66


def test_purchased_carrier_amounts(sut):
    pass  # TODO #66


def test_used_carriers(sut):
    pass  # TODO #66


def test_products(sut):
    pass  # TODO #66


def test_by_products(sut):
    pass  # TODO #66


def test_used_process_ids(sut):
    pass  # TODO #66


def test_optimize(sut, energy_carrier, product, optimization_context):
    sut.optimize(2000, optimization_context)
    result = sut.optimization_results

    purchased_carrier_amounts = result.purchased_carrier_amounts
    assert purchased_carrier_amounts[energy_carrier] == 0
    assert purchased_carrier_amounts[product] == 1

    process_execution_counts = result.process_execution_counts

    available_process_options = sut.available_process_options
    process_option = available_process_options[0]
    installed_process_option = available_process_options[1]

    assert process_execution_counts[process_option] == 0
    assert process_execution_counts[installed_process_option] == 0


def test_accept(sut):
    pass  # TODO #66


def test_consume_purchased_carrier_amounts(sut):
    pass  # TODO #66


def test_export_produced_carrier_amounts(sut):
    pass  # TODO #66


def test_sell_gain_in_euro(sut):
    pass  # TODO #66


def test_export(sut):
    pass  # TODO #66


def test_new_investment_in_euro(sut):
    pass  # TODO #66


def test_pipeline_cost_in_euro(sut):
    pass  # TODO #66


def test_pipeline_cost_scaling_factor(sut):
    pass  # TODO #66


def test_carrier_purchase_cost_in_euro(sut):
    pass  # TODO #66


def test_carrier_availability(sut):
    pass  # TODO #66


def test_carrier_minimum_export_in_t(sut, product, simulation_options):
    result = sut.carrier_minimum_export_in_t(product, simulation_options['start_year'], simulation_options)
    assert result == 1


def test_carrier_minimum_use(sut):
    pass  # TODO #66


def test_upstream_emission_in_t_co2(sut):
    pass  # TODO #66


def test_number_of_process_usages(sut):
    pass  # TODO #66


def test_maximum_production_limits(sut, optimization_context, product):
    sut.optimize(2000, optimization_context)
    export = sut.export(2000)
    assert export[product] <= product.maximum_production_in_unit
