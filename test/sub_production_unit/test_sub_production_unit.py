# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import Mock, fixture, patch, patch_property

from by_product.by_product import ByProduct
from energy_carrier.energy_carrier import EnergyCarrier
from sub_production_unit.sub_production_unit import SubProductionUnit


@fixture
def sut():
    id_sub_production_unit = 1
    id_production_unit = 1
    process_execution_count = 10
    max_process_execution_count = 100
    year_of_last_reinvestment = 2020

    sub_production_unit = SubProductionUnit(
        id_sub_production_unit,
        id_production_unit,
        process_execution_count,
        max_process_execution_count,
        year_of_last_reinvestment,
    )
    sub_production_unit.installed_process = Mock()
    return sub_production_unit


def test_construction(sut):
    assert sut is not None


def test_id_production_unit_exposes_the_owning_production_unit(sut):
    """Should expose the owning production unit ID as a property, not as a public attribute."""
    assert sut.id_production_unit == 1


def test_id_production_unit_can_be_reassigned(sut):
    """Should allow re-parenting, which happens when sites are merged into a group."""
    sut.id_production_unit = 42

    assert sut.id_production_unit == 42


def test_used_carriers(sut):
    sut.installed_process = Mock()
    sut.installed_process.used_carriers = 'mocked_carriers'
    result = sut.used_carriers
    assert result == 'mocked_carriers'


def test_output_by_products(sut):
    sut.installed_process = Mock()
    sut.installed_process.output_by_products = 'mocked_by_products'
    result = sut.output_by_products
    assert result == 'mocked_by_products'


def test_id_process(sut):
    sut.installed_process = Mock()
    sut.installed_process.id = 'mocked_id'
    result = sut.id_process
    assert result == 'mocked_id'


def test_demands(sut):
    sut.installed_process = Mock()
    sut.installed_process.demands = 'mocked_demands'
    result = sut.demands
    assert result == 'mocked_demands'


def test_accept(sut):
    sut.installed_process = Mock()
    visitor = Mock()
    sut.accept(visitor, 2020)
    assert visitor.enter_sub_production_unit.called
    assert sut.installed_process.accept.called
    assert visitor.exit_sub_production_unit.called


def test_netto_produced_or_consumed_amount_for_carrier(sut):
    sut.installed_process = Mock()
    sut.installed_process.netto_produced_or_consumed_amount_per_process_count = Mock(5)
    result = sut.netto_produced_or_consumed_amount_for_carrier(2020, 'mocked_carrier')
    assert result == 50


@patch(SubProductionUnit._process_production_cost_in_euro, 2)
@patch(SubProductionUnit._direct_emission_cost_in_euro, 3)
def test_production_cost_in_euro(sut):
    result = sut.production_cost_in_euro(
        2020,
        'mocked_co2_cost_in_euro_per_t_co2',
        0.05,
        'mocked_simulation_options',
    )
    assert result == 2 + 3


def test_annuity_on_investment_in_euro(sut):
    sut.installed_process = Mock()
    sut.installed_process.annuity_on_investment_in_euro_per_process_count = Mock(20)
    sut.max_process_execution_count = 10
    result = sut.annuity_on_investment_in_euro(2020, 0.05, 'mocked_simulation_options')
    assert result == 200


def test_annuity_on_investment_in_euro_before_reinvestment_year_is_zero(sut):
    sut.installed_process = Mock()
    sut.installed_process.annuity_on_investment_in_euro_per_process_count = Mock(20)
    sut.max_process_execution_count = 10
    sut.year_of_last_reinvestment = 2025
    result = sut.annuity_on_investment_in_euro(2024, 0.05, 'mocked_simulation_options')
    assert result == 0


def test_opex_in_euro(sut):
    sut.installed_process = Mock()
    sut.installed_process.opex_in_euro_per_process_count = Mock(20)
    sut.process_execution_count = 10
    result = sut.opex_in_euro(2020, 'mocked_simulation_options')
    assert result == 200


class TestNewInvestmentInEuro:
    def test_year_of_last_reinvestment(self, sut):
        sut.installed_process = Mock()
        sut.installed_process.net_capex_in_euro_per_process_count = Mock(20)
        sut.process_execution_count = 0
        sut.max_process_execution_count = 15
        result = sut.new_investment_in_euro(2020, 'mocked_simulation_options')
        assert result == 300

    def test_different_year(self, sut):
        result = sut.new_investment_in_euro(2019, 'mocked_simulation_options')
        assert result == 0


class TestNumberOfProcessUsages:
    def test_is_not_used(self, sut):
        process = Mock()
        process.id = 1
        result = sut.number_of_process_usages(process)
        assert result == 0

    def test_is_used(self, sut):
        process = Mock()
        process.id = 2
        sut.installed_process = process
        result = sut.number_of_process_usages(process)
        assert result == 1

    def test_does_not_exist(self, sut):
        dummy = {}
        result = sut.number_of_process_usages(dummy)
        assert result == 0


def test_direct_emissions_in_t_co2(sut):
    sut.installed_process = Mock()
    sut.installed_process.emission = Mock()
    sut.installed_process.emission.direct_emissions_in_t_co2 = Mock('mocked_result')
    result = sut.direct_emissions_in_t_co2(2025)
    assert result == 'mocked_result'


def test_emissions_in_t_co2(sut):
    with pytest.raises(NotImplementedError):
        sut.emissions_in_t_co2()


def test_process_production_cost_in_euro(sut):
    sut.installed_process = Mock()
    sut.installed_process.production_cost_in_euro_per_process_count = Mock(20)
    sut.process_execution_count = 10
    result = sut._process_production_cost_in_euro(2020, 0.05, 'mocked_simulation_options')
    assert result == 200


def test_direct_emission_cost_in_euro(sut):
    sut.process_execution_count = 10
    sut.installed_process = Mock()
    sut.installed_process.emission = Mock()
    sut.installed_process.emission.direct_emissions_in_t_co2_per_process_count = Mock(0.5)
    result = sut._direct_emission_cost_in_euro(2020, 10)
    assert result == 50  # 0.5  * 10 * 10


def test_uses_carrier(sut):
    first_carrier = EnergyCarrier(1, 'first_carrier', Mock())
    second_carrier = ByProduct(2, 'second_carrier', Mock())
    third_carrier = EnergyCarrier(2, 'third_carrier', Mock())

    with patch_property(SubProductionUnit.used_carriers, [first_carrier, second_carrier, third_carrier]):
        result = sut._uses_carrier(EnergyCarrier, 2)
        assert result is True

        result = sut._uses_carrier(EnergyCarrier, 3)
        assert result is False


def test_cost_bases_differ_in_the_fixture(sut):
    """
    Guard for the three tests below: they can only tell the confirmed behavior apart
    from the rejected one if the installed capacity differs from the actual
    utilization. `sub_production_unit_factory` has a construction path that makes the
    two equal, which would silently make the pinning tests vacuous.
    """
    assert sut.max_process_execution_count != sut.process_execution_count


def test_annuity_is_charged_on_installed_capacity(sut):
    """
    Pins a deliberate modeling decision, confirmed by the domain owner in
    `bd show forecast-sites-private-6zj.12`: capital costs are charged on installed
    capacity, so the annuity scales with `max_process_execution_count` and not with the
    actual `process_execution_count`. Do not "harmonize" this with the opex base below.
    """
    annuity_per_count = 7.0
    sut.installed_process.annuity_on_investment_in_euro_per_process_count = Mock(annuity_per_count)

    result = sut.annuity_on_investment_in_euro(2025, 0.05, 'mocked_simulation_options')

    assert result == pytest.approx(sut.max_process_execution_count * annuity_per_count)


def test_opex_is_charged_on_actual_utilization(sut):
    """
    Counterpart to the annuity test and part of the same decision: variable costs are
    charged on actual utilization, so opex scales with `process_execution_count` and not
    with the installed `max_process_execution_count`.
    """
    opex_per_count = 3.0
    sut.installed_process.opex_in_euro_per_process_count = Mock(opex_per_count)

    result = sut.opex_in_euro(2025, 'mocked_simulation_options')

    assert result == pytest.approx(sut.process_execution_count * opex_per_count)


def test_new_investment_is_charged_on_installed_capacity(sut):
    """
    Third part of the same decision: a new investment is a capital cost, so it scales
    with `max_process_execution_count`. The year must equal `year_of_last_reinvestment`,
    otherwise no investment falls due at all.
    """
    capex_per_count = 11.0
    sut.installed_process.net_capex_in_euro_per_process_count = Mock(capex_per_count)

    result = sut.new_investment_in_euro(sut.year_of_last_reinvestment, 'mocked_simulation_options')

    assert result == pytest.approx(sut.max_process_execution_count * capex_per_count)
