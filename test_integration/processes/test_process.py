# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from _pytest.python_api import approx
from test_utils.isi_mock import fixture


@fixture
def sut(process):
    return process


@fixture
def year():
    return 2000


def test_construction(sut):
    assert sut is not None


def test__repr__(sut):
    result = repr(sut)
    assert result == 'Process(id=1)'


def test_demands(sut):
    result = sut.demands
    assert len(result) == 1
    demand = result[0]
    assert demand.carrier.name == 'Electricity'


def test_outputs(sut):
    result = sut.outputs
    assert len(result) == 1
    output = result[0]
    assert output.product.name == 'Steel'


def test_lifetime_in_years(sut):
    result = sut.lifetime_in_years
    assert result == 20


def test_depreciation_period(sut):
    result = sut.depreciation_period
    assert result == 15


def test_non_energy_direct_process_emission_in_t_co2_per_process_count(sut):
    result = sut.non_energy_direct_process_emission_in_t_co2_per_process_count
    assert result == approx(0.05)


def test_capex_interpolation_data_in_euro_per_process_count(sut):
    result = sut.capex_interpolation_data_in_euro_per_process_count
    assert result.value_for_start_year == 2_000_000
    assert result.value_for_end_year == 2_200_000


def test_opex_interpolation_data_in_euro_per_process_count(sut):
    result = sut.opex_interpolation_data_in_euro_per_process_count
    assert result.value_for_start_year == 150_000
    assert result.value_for_end_year == 140_000


def test_investment_funding_interpolation_data_in_euro_per_process_count(sut):
    result = sut.investment_funding_interpolation_data_in_euro_per_process_count
    assert result.value_for_start_year == 0
    assert result.value_for_end_year == 250_000


def test_efficiency_improvement_interpolation_data(sut):
    result = sut.efficiency_improvement_interpolation_data
    assert result.value_for_start_year == 0
    assert result.value_for_end_year == 0.1


def test_compound_factor(sut, region):
    interest_rate = region.interest_rate
    result = sut._compound_factor(interest_rate)
    assert result == approx(2.07892, 1e-5)  # (1 + 0.05) ** 15


def test_annuity_factor(sut, region):
    interest_rate = region.interest_rate
    result = sut._annuity_factor(interest_rate)
    assert result == approx(0.096342, 1e-5)  # 0.05 * 2.07892 / (2.07892 - 1)


def test_used_carriers(sut):
    result = sut.used_carriers
    assert len(result) == 2
    carrier = result[0]
    assert carrier.name == 'Electricity'


def test_output_carriers(sut):
    result = sut.output_carriers
    assert len(result) == 1
    carrier = result[0]
    assert carrier.name == 'Steel'


def test_output_products(sut):
    result = sut.output_products
    assert len(result) == 1
    output_product = result[0]
    assert output_product.name == 'Steel'


def test_output_by_products(sut):
    result = sut.output_by_products
    assert len(result) == 0


def test_emission(sut):
    result = sut.emission
    assert result is not None


def test_accept(sut):
    class ProcessVisitor:
        def __init__(self):
            self.visited_process_ids = []

        def enter_process(self, process, _year):
            self.visited_process_ids.append(process.id)

        def exit_process(self, process, year, enter_results, child_results):
            pass

        def enter_output(self, output, year):
            pass

        def exit_output(self, output, year, enter_results):
            pass

    visitor = ProcessVisitor()
    sut.accept(visitor, 2020)

    assert visitor.visited_process_ids == [1]


def test_netto_produced_or_consumed_amount_per_process_count(sut, year):
    carrier = sut.demands[0].carrier  # Electricity
    result = sut.netto_produced_or_consumed_amount_per_process_count(year, carrier)
    assert result == -200

    carrier = sut.outputs[0].carrier  # Steel
    result = sut.netto_produced_or_consumed_amount_per_process_count(year, carrier)
    assert result == 10


def test_production_in_gj(sut):
    carrier = sut.demands[0].carrier  # Electricity
    result = sut.production_in_gj(carrier, 10)
    assert result == 0


def test_net_capex_in_euro_per_process_count(sut, simulation_options):
    result = sut.net_capex_in_euro_per_process_count(2000, simulation_options)
    assert result == approx(2e6)  # 2e6 - 0


def test_annual_cost_in_euro_per_process_count(
    sut,
    co2_price_in_euro_per_t_co2,
    simulation_options,
):
    result = sut.annual_cost_in_euro_per_process_count(2000, co2_price_in_euro_per_t_co2, simulation_options)
    assert result == 153705  # 150_000 - -3700 + 5


def test_invest_cost_in_euro_per_process_count(sut, simulation_options, region):
    interest_rate = region.interest_rate
    result = sut.invest_cost_in_euro_per_process_count(2000, interest_rate, simulation_options)
    # Returning capex value at start year
    assert result == approx(2000000.0, 1e-1)  # 2e6


def test_year_of_new_investment(sut):
    pass  # TODO: #66 apply or remove unused function


def test_production_cost_in_euro_per_process_count(sut, simulation_options, region):
    interest_rate = region.interest_rate
    result = sut.production_cost_in_euro_per_process_count(2000, interest_rate, simulation_options)
    # annuity + opex + purchase = 192684 + 150000 + 8400 = 350684
    assert result == approx(350684, 1e-1)  # 192684 + 150_000 + 8400


def test_annuity_on_investment_in_euro_per_process_count(sut, simulation_options, region):
    interest_rate = region.interest_rate
    result = sut.annuity_on_investment_in_euro_per_process_count(2000, interest_rate, simulation_options)
    assert result == approx(192684, 1e-1)  # 0.096342 * (2e6 - 0)


def test_purchase_cost_in_euro_per_process_count(sut):
    result = sut.purchase_cost_in_euro_per_process_count(2000)
    # purchase cost is raw only: 8400
    assert result == approx(8400)


def test_capex_in_euro_per_process_count(sut, simulation_options):
    result = sut.capex_in_euro_per_process_count(2000, simulation_options)
    assert result == approx(2e6)


def test_opex_in_euro_per_process_count(sut, simulation_options):
    result = sut.opex_in_euro_per_process_count(2000, simulation_options)
    assert result == approx(0.15e6)


def test_subsidies_in_euro_per_process_count(sut, simulation_options):
    result = sut.subsidies_in_euro_per_process_count(2000, simulation_options)
    assert result == approx(400)


def test_taxes_in_euro_per_process_count(sut, simulation_options):
    result = sut.taxes_in_euro_per_process_count(2000, simulation_options)
    assert result == approx(1200)
