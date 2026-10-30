# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Targeted coverage tests for InstalledProcess - missing branches.
Focus: Private method calculations and boundary conditions (96% coverage)
"""

import pytest
from test_utils.isi_mock import Mock
from test_utils.process_data_stub import make_process_data_stub

from processes.installed_process import InstalledProcess


@pytest.fixture
def installed_process():
    """Create a test InstallProcess instance"""
    process = make_process_data_stub(
        demands=(),
        outputs=(),
        carbon_capture_rate=0.0,
        sector_ids=(1,),
        lifetime_in_years=15,
        depreciation_period=30,
        non_energy_direct_process_emission_in_t_co2_per_process_count=0,
        capex_interpolation_data_in_euro_per_process_count=Mock(),
        opex_interpolation_data_in_euro_per_process_count=Mock(),
        investment_funding_interpolation_data_in_euro_per_process_count=Mock(),
        efficiency_improvement_interpolation_data=Mock(),
    )
    process.id = 101
    process.depreciation_period = 30

    sub_unit = Mock()
    sub_unit.max_process_execution_count = 100
    sub_unit.year_of_last_reinvestment = 2020

    return InstalledProcess(process, sub_unit)


class TestInstalledProcessCoverageMissingBranches:
    """Tests for missing branches in InstalledProcess (96% coverage)"""

    def test_planning_years_correct_range(self, installed_process):
        """Test: Planning years span from current to end year inclusive"""
        simulation_options = {'rolling_planning_horizon_in_years': 5}

        planning_years = InstalledProcess._planning_years(2025, simulation_options)

        assert planning_years[0] == 2025
        assert planning_years[-1] == 2030
        assert len(planning_years) == 6

    def test_planning_years_longer_horizon(self, installed_process):
        """Test: Planning years works with various horizons"""
        simulation_options = {'rolling_planning_horizon_in_years': 10}

        planning_years = InstalledProcess._planning_years(2000, simulation_options)

        assert len(planning_years) == 11
        assert planning_years[-1] == 2010

    def test_capex_age_factor_is_zero_within_lifetime(self, installed_process):
        """Test: no repair costs are charged while the process is within its lifetime"""
        assert installed_process._capex_age_factor(0) == 0
        assert installed_process._capex_age_factor(installed_process.lifetime_in_years) == 0

    def test_capex_age_factor_grows_linearly_beyond_lifetime(self, installed_process):
        """Test: repair costs rise linearly with life_extension_factor once the lifetime is exceeded"""
        lifetime = installed_process.lifetime_in_years
        factor = installed_process.life_extension_factor

        assert installed_process._capex_age_factor(lifetime + 1) == pytest.approx(factor)
        assert installed_process._capex_age_factor(lifetime + 10) == pytest.approx(factor * 10)

    def test_opex_age_factor_formula(self, installed_process):
        """Test: _opex_age_factor = 1 + age/10000"""
        assert installed_process._opex_age_factor(2020) == 1.0
        assert installed_process._opex_age_factor(2025) == pytest.approx(1.0005)
        assert installed_process._opex_age_factor(2030) == pytest.approx(1.001)

    def test_age_at_reinvestment_year(self, installed_process):
        """Test: Age is 0 in reinvestment year"""
        installed_process._sub_production_unit.year_of_last_reinvestment = 2025

        assert installed_process._age(2025) == 0

    def test_age_after_reinvestment(self, installed_process):
        """Test: Age increments linearly after reinvestment"""
        installed_process._sub_production_unit.year_of_last_reinvestment = 2020

        assert installed_process._age(2020) == 0
        assert installed_process._age(2021) == 1
        assert installed_process._age(2025) == 5
        assert installed_process._age(2030) == 10

    def test_age_before_reinvestment(self, installed_process):
        """Test: Age is negative before reinvestment year"""
        installed_process._sub_production_unit.year_of_last_reinvestment = 2025

        assert installed_process._age(2020) == -5
        assert installed_process._age(2024) == -1

    def test_annuity_at_depreciation_boundary(self, installed_process):
        """Test: Returns 0 at depreciation period boundary"""
        installed_process._sub_production_unit.year_of_last_reinvestment = 2020
        # Age = 30 years = depreciation_period

        result = installed_process.annuity_on_investment_in_euro_per_process_count(2050, 0.05, {})
        assert result == 0

    def test_annuity_after_depreciation(self, installed_process):
        """Test: Returns 0 after depreciation period"""
        installed_process._sub_production_unit.year_of_last_reinvestment = 2020
        # Age = 40 years > 30 year depreciation period

        result = installed_process.annuity_on_investment_in_euro_per_process_count(2060, 0.05, {})
        assert result == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
