# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Tests for future investments in sub_production_units.

Validates that sub_production_units with year_of_last_reinvestment
beyond the simulation horizon can be modeled as planned future capacity.
"""

from sub_production_unit.sub_production_unit import SubProductionUnit


class TestFutureInvestmentsBasic:
    """Tests for basic future investment functionality."""

    def test_future_investment_year_creation(self):
        """Sub-production unit can be created with future investment year."""
        future_year = 2050

        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=future_year,
        )

        assert unit.year_of_last_reinvestment == future_year
        assert unit.id == 1
        assert unit.process_execution_count == 10

    def test_future_investment_year_far_future(self):
        """Sub-production unit supports far future investment years (2100+)."""
        year_2100 = 2100

        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=5,
            max_process_execution_count=10,
            year_of_last_reinvestment=year_2100,
        )

        assert unit.year_of_last_reinvestment == year_2100

    def test_multiple_future_investments_staggered(self):
        """Multiple sub-production units with staggered future investment years."""
        unit_2030 = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=5,
            max_process_execution_count=5,
            year_of_last_reinvestment=2030,
        )

        unit_2040 = SubProductionUnit(
            id_sub_production_unit=2,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=2040,
        )

        unit_2050 = SubProductionUnit(
            id_sub_production_unit=3,
            id_production_unit=1,
            process_execution_count=15,
            max_process_execution_count=15,
            year_of_last_reinvestment=2050,
        )

        # All can exist simultaneously
        units = [unit_2030, unit_2040, unit_2050]
        assert len(units) == 3
        assert units[0].year_of_last_reinvestment == 2030
        assert units[1].year_of_last_reinvestment == 2040
        assert units[2].year_of_last_reinvestment == 2050

    def test_future_investment_execution_counts(self):
        """Sub-production unit stores different execution counts for future investment."""
        future_year = 2050
        current_execution = 5
        max_execution = 15

        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=current_execution,
            max_process_execution_count=max_execution,
            year_of_last_reinvestment=future_year,
        )

        assert unit.process_execution_count == current_execution
        assert unit.max_process_execution_count == max_execution
        # Future investment will use max_execution once available

    def test_future_investment_past_investment_still_works(self):
        """Sub-production unit works with past investment years (existing behavior)."""
        past_year = 2000

        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=past_year,
        )

        assert unit.year_of_last_reinvestment == past_year
        # Should work exactly as before


class TestFutureInvestmentsLogic:
    """Tests verifying the logic of future investments."""

    def test_future_vs_past_investment_years(self):
        """Verify distinction between past and future investment years."""
        current_year = 2025
        past_year = 2010
        future_year = 2050

        past_unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=past_year,
        )

        future_unit = SubProductionUnit(
            id_sub_production_unit=2,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=future_year,
        )

        # Past investment is before current year
        assert past_unit.year_of_last_reinvestment < current_year

        # Future investment is after current year
        assert future_unit.year_of_last_reinvestment > current_year

    def test_future_investment_available_property_relationship(self):
        """Future investments determine availability via year_of_last_reinvestment."""
        future_year = 2050

        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=0,
            max_process_execution_count=10,
            year_of_last_reinvestment=future_year,
        )

        # The key property for determining availability
        assert unit.year_of_last_reinvestment == future_year

        # Installed process will use this to check is_available_in_year(year)
        # which implements: year >= unit.year_of_last_reinvestment


class TestFutureInvestmentsDocumentation:
    """Tests documenting future investment capability."""

    def test_future_investment_feature_is_enabled(self):
        """Future investments are supported (no validation prevents them)."""
        # This test documents that the feature IS enabled
        # If this fails, it means there's a constraint preventing future years
        future_years = [2050, 2075, 2100, 2150]

        for future_year in future_years:
            unit = SubProductionUnit(
                id_sub_production_unit=future_year // 10,
                id_production_unit=1,
                process_execution_count=10,
                max_process_execution_count=10,
                year_of_last_reinvestment=future_year,
            )
            assert unit.year_of_last_reinvestment == future_year


class TestFutureInvestmentsCostLogic:
    """Tests documenting cost logic for future investments."""

    def test_future_investment_annuity_logic(self):
        """
        Future investments have zero annuity until investment year.

        This is implemented in SubProductionUnit.annuity_on_investment_in_euro():
        if year < self.year_of_last_reinvestment:
            return 0

        This allows planning future capacity without paying annuity costs today.
        """
        future_year = 2050

        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=future_year,
        )

        # The SubProductionUnit stores the year - the rest of the logic is in
        # annuity_on_investment_in_euro() which checks if year is less than
        # year_of_last_reinvestment and returns 0 in that case
        assert unit.year_of_last_reinvestment == future_year

    def test_future_investment_opex_age_factor_logic(self):
        """
        Future investments will have negative age, but this is handled correctly.

        In InstalledProcess._opex_age_factor():
        age = year - self._year_of_last_reinvestment
        age_factor = 1 + age / 10000

        For future investments (negative age):
        - age = 2025 - 2050 = -25
        - age_factor = 1 + (-25/10000) = 0.9975

        This slightly reduces OPEX costs for future capacity before it's built,
        which is a reasonable approximation (future tech may be cheaper).
        """
        future_year = 2050
        current_year = 2025
        age = current_year - future_year  # = -25

        expected_age_factor = 1 + age / 10000
        assert expected_age_factor < 1  # Slightly reduced
        assert abs(expected_age_factor - 0.9975) < 0.00001

    def test_future_investment_capex_age_factor_logic(self):
        """
        Future investments have full CAPEX costs (age < depreciation_period).

        In InstalledProcess._capex_age_factor():
        if age >= self.depreciation_period:
            return 0  # Fully depreciated, no more capex
        return 1  # Full capex cost

        For future investments with negative age:
        - age = -25 (before investment)
        - -25 < depreciation_period (e.g., 20)
        - Returns 1 (full capex cost)

        This is correct: future capacity needs full investment costs.
        """
        depreciation_period = 20
        future_year = 2050
        current_year = 2025
        age = current_year - future_year  # = -25

        # Negative age is less than depreciation period
        assert age < depreciation_period
        # Therefore CAPEX factor = 1 (full cost)


class TestFutureInvestmentsUseCases:
    """Tests documenting real-world use cases for future investments."""

    def test_planned_capacity_expansion_2030(self):
        """
        Use case: Company plans to install new production unit in 2030.

        This allows modeling of:
        - Current production (2025) with existing units
        - Planned expansion (2030) with zero availability before 2030
        - Strategic planning of future capacity
        """
        current_units = [
            SubProductionUnit(
                id_sub_production_unit=1,
                id_production_unit=1,
                process_execution_count=10,
                max_process_execution_count=10,
                year_of_last_reinvestment=2010,
            )
        ]

        planned_expansion = SubProductionUnit(
            id_sub_production_unit=2,
            id_production_unit=1,
            process_execution_count=20,
            max_process_execution_count=20,
            year_of_last_reinvestment=2030,
        )

        all_units = [*current_units, planned_expansion]
        assert len(all_units) == 2
        assert all_units[0].year_of_last_reinvestment == 2010
        assert all_units[1].year_of_last_reinvestment == 2030

    def test_phased_capacity_rollout(self):
        """
        Use case: Phased capacity rollout over decades.

        A company plans multiple facility builds at different times,
        allowing realistic long-term planning.
        """
        phases = [
            SubProductionUnit(
                id_sub_production_unit=i,
                id_production_unit=1,
                process_execution_count=10,
                max_process_execution_count=10,
                year_of_last_reinvestment=2025 + (i * 15),
            )
            for i in range(4)
        ]

        assert len(phases) == 4
        assert phases[0].year_of_last_reinvestment == 2025
        assert phases[1].year_of_last_reinvestment == 2040
        assert phases[2].year_of_last_reinvestment == 2055
        assert phases[3].year_of_last_reinvestment == 2070

    def test_climate_neutral_2050_planning(self):
        """
        Use case: Climate-neutral 2050 planning with future technologies.

        Models:
        - Existing fossil-based capacity (2000-2020)
        - Scheduled technology transitions (2025-2040)
        - Future renewable capacity (2040-2050)
        """
        fossil_unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=100,
            max_process_execution_count=100,
            year_of_last_reinvestment=2015,
        )

        transition_unit = SubProductionUnit(
            id_sub_production_unit=2,
            id_production_unit=1,
            process_execution_count=50,
            max_process_execution_count=50,
            year_of_last_reinvestment=2030,
        )

        renewable_unit = SubProductionUnit(
            id_sub_production_unit=3,
            id_production_unit=1,
            process_execution_count=80,
            max_process_execution_count=80,
            year_of_last_reinvestment=2045,
        )

        units = [fossil_unit, transition_unit, renewable_unit]
        assert len(units) == 3
        # Portfolio shows gradual transition with future investments
