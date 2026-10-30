# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import Mock, fixture, original_patch, patch, patch_property
from test_utils.process_data_stub import make_process_data_stub

from processes.installed_process import InstalledProcess
from processes.process import Process


@fixture
def sut():
    process = make_process_data_stub(
        demands=(),
        outputs=(),
        carbon_capture_rate=0.0,
        sector_ids=(1,),
        lifetime_in_years=15,
        depreciation_period=5,
        non_energy_direct_process_emission_in_t_co2_per_process_count=0,
        capex_interpolation_data_in_euro_per_process_count=Mock(),
        opex_interpolation_data_in_euro_per_process_count=Mock(),
        investment_funding_interpolation_data_in_euro_per_process_count=Mock(),
        efficiency_improvement_interpolation_data=Mock(),
    )
    process.id = 101
    process.demands = ()
    process.outputs = ()
    process.carbon_capture_rate = 0.0
    process.sector_ids = (1,)
    process.lifetime_in_years = 15
    process.tech_avaiable_at_year = 2020
    process.life_extension_factor = 0.5
    process.interest_rate = 0.05
    process.depreciation_period = 5
    process.non_energy_direct_process_emission_in_t_co2_per_process_count = 0
    process.capex_interpolation_data_in_euro_per_process_count = Mock()
    process.opex_interpolation_data_in_euro_per_process_count = Mock()
    process.investment_funding_interpolation_data_in_euro_per_process_count = Mock()
    process.efficiency_improvement_interpolation_data = Mock()

    sub_production_unit = Mock()
    sub_production_unit.max_process_execution_count = 9
    sub_production_unit.year_of_last_reinvestment = 2020
    return InstalledProcess(process, sub_production_unit)


def test_construction(sut):
    assert sut is not None


def test__repr__(sut):
    result = sut.__repr__()
    assert result == 'InstalledProcess(101|2020)'


def test_available_process_execution_count_in_reinvestment_year(sut):
    sut._sub_production_unit.max_process_execution_count = 7
    result = sut.available_process_execution_count(2020)
    assert result == 7


def test_available_process_execution_count_after_reinvestment_year(sut):
    sut._sub_production_unit.max_process_execution_count = 7
    result = sut.available_process_execution_count(2021)
    assert result == 7


def test_available_process_execution_count_before_reinvestment_year(sut):
    sut._sub_production_unit.max_process_execution_count = 7
    sut._sub_production_unit.year_of_last_reinvestment = 2025
    result = sut.available_process_execution_count(2024)
    assert result == 0


def test_is_available_in_year_before_reinvestment_year(sut):
    sut._sub_production_unit.year_of_last_reinvestment = 2025
    result = sut.is_available_in_year(2024)
    assert result is False


def test_is_available_in_year_in_reinvestment_year(sut):
    sut._sub_production_unit.year_of_last_reinvestment = 2025
    result = sut.is_available_in_year(2025)
    assert result is True


def test_year_of_last_reinvestment(sut):
    sut._sub_production_unit.year_of_last_reinvestment = 2018
    result = sut._year_of_last_reinvestment
    assert result == 2018


# Repair cost over the two planning years 2023 and 2024, with an age factor of 0.5 and a raw CAPEX
# of 100: 0.5 * 100 / 1.05^0 + 0.5 * 100 / 1.05^1. The three tests below must all reach this same
# value -- that agreement is what pins the behavior.
UNFUNDED_REPAIR_COST_IN_EURO = 97.61904761904762


@patch(InstalledProcess._capex_age_factor, 0.5)
@patch(InstalledProcess.capex_in_euro_per_process_count, 100)
def test_invest_cost_in_euro_per_process_count(sut):
    result = sut.invest_cost_in_euro_per_process_count(
        2023,
        0.05,
        {'rolling_planning_horizon_in_years': 1},
    )
    assert result == pytest.approx(UNFUNDED_REPAIR_COST_IN_EURO, rel=1e-6)


@patch(InstalledProcess._capex_age_factor, 0.5)
@patch(InstalledProcess.capex_in_euro_per_process_count, 100)
@patch(Process.investment_funding_in_euro_per_process_count, 10_000)
def test_invest_cost_ignores_the_investment_funding(sut):
    """
    Pins a deliberate modeling decision, confirmed by the domain owner in
    `bd show forecast-sites-private-6zj.19`: investment funding reduces the cost of
    *new* plants only. The age-dependent repair cost is computed from the raw CAPEX, so
    a funding large enough to wipe the cost out entirely leaves it untouched. Do not
    route this through `net_capex_in_euro_per_process_count`.
    """
    result = sut.invest_cost_in_euro_per_process_count(
        2023,
        0.05,
        {'rolling_planning_horizon_in_years': 1},
    )

    assert result == pytest.approx(UNFUNDED_REPAIR_COST_IN_EURO, rel=1e-6)


@patch(InstalledProcess._capex_age_factor, 0.5)
@patch(InstalledProcess.capex_in_euro_per_process_count, 100)
def test_invest_cost_ignores_the_start_year_capex_factor(sut):
    """
    Pins that an installed process ignores `capex_factor`, hence the parameter name
    `_capex_factor`. The start year factor penalizes switching to a *new* process, so
    scaling an existing plant's repair cost by it would be wrong. Because the process
    discards the factor itself, callers pass it unconditionally and need no `isinstance`
    check; see `bd show forecast-sites-private-6zj.18` and src/AGENTS.md.
    """
    result = sut.invest_cost_in_euro_per_process_count(
        2023,
        0.05,
        {'rolling_planning_horizon_in_years': 1},
        5.0,
    )

    assert result == pytest.approx(UNFUNDED_REPAIR_COST_IN_EURO, rel=1e-6)


def test_planning_years():
    result = InstalledProcess._planning_years(2023, {'rolling_planning_horizon_in_years': 2})
    assert result == [2023, 2024, 2025]


@patch(Process.capex_in_euro_per_process_count, 'mocked_result')
def test_capex_in_euro_per_process_count(sut):
    result = sut.capex_in_euro_per_process_count(2025, {})
    assert result == 'mocked_result'


@patch(Process.opex_in_euro_per_process_count, 200)
@patch(InstalledProcess._opex_age_factor, 0.5)
def test_opex_in_euro_per_process_count(sut):
    result = sut.opex_in_euro_per_process_count(2025, {})
    assert result == 100


class TestCapexAgeFactor:
    def test_age_within_lifetime_returns_zero(self, sut):
        # sut fixture: lifetime=15, life_extension_factor=0.5
        # age=10 < lifetime=15 → factor = 0
        result = sut._capex_age_factor(10)
        assert result == 0

    def test_age_at_lifetime_returns_zero(self, sut):
        # sut fixture: lifetime=15, life_extension_factor=0.5
        # age=15 == lifetime=15 → factor = 0 (boundary: age <= lifetime)
        result = sut._capex_age_factor(15)
        assert result == 0

    def test_age_beyond_lifetime_returns_rising_factor(self, sut):
        # sut fixture: lifetime=15, life_extension_factor=0.5
        # age=17 > lifetime=15, factor = 0.5 * (17-15) = 1.0
        result = sut._capex_age_factor(17)
        assert result == pytest.approx(1.0)

    def test_age_well_beyond_lifetime(self, sut):
        # sut fixture: lifetime=15, life_extension_factor=0.5
        # age=25 > lifetime=15, factor = 0.5 * (25-15) = 5.0
        result = sut._capex_age_factor(25)
        assert result == pytest.approx(5.0)


@patch(InstalledProcess._age, 12)
def test_opex_age_factor(sut):
    result = sut._opex_age_factor('mocked_year')
    assert result == 1.0012


@patch_property(InstalledProcess._year_of_last_reinvestment, 2000)
def test_age(sut):
    result = sut._age(2025)
    assert result == 25


class TestAnnuityOnInvestment:
    """Tests for annuity_on_investment_in_euro_per_process_count method."""

    @patch_property(InstalledProcess.depreciation_period, 10)
    @patch(InstalledProcess._age, 5)  # Age less than depreciation period
    def test_returns_parent_value_when_before_depreciation_period(self, sut):
        """When age < depreciation_period, delegate to parent implementation."""
        # Parent returns annuity factor * capex - funding
        parent_result = 123.45
        with original_patch.object(
            InstalledProcess.__bases__[0],
            'annuity_on_investment_in_euro_per_process_count',
            Mock(return_value=parent_result),
        ):
            result = sut.annuity_on_investment_in_euro_per_process_count(2020, 0.05, {})
            assert result == parent_result

    @patch_property(InstalledProcess.depreciation_period, 10)
    @patch(InstalledProcess._age, 12)  # Age greater than depreciation period
    def test_returns_zero_when_past_depreciation_period(self, sut):
        """When age >= depreciation_period, return 0 (equipment fully depreciated)."""
        result = sut.annuity_on_investment_in_euro_per_process_count(2020, 0.05, {})
        assert result == 0
