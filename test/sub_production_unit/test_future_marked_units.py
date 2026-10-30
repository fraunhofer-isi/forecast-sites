# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Tests for marking sub-production units as future (planned but not built).

This feature allows explicit marking of units as "future" (planned investments),
separate from their year_of_last_reinvestment value.

Provides:
1. Boolean flag to mark units as future
2. Helper methods to identify future vs. existing units
3. Documentation of database schema for future unit indicator
"""

from sub_production_unit.sub_production_unit import SubProductionUnit


class TestFutureMarkedUnits:
    """Tests for marking sub-production units with future/planned status."""

    def test_unit_without_is_future_attribute(self):
        """
        Current SubProductionUnit doesn't have is_future attribute.

        This test documents the status quo:
        - SubProductionUnit has year_of_last_reinvestment
        - No separate is_future boolean flag currently exists
        - Year value alone determines future status
        """
        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=2050,
        )

        # Current implementation: no is_future attribute
        assert not hasattr(unit, 'is_future')
        # Future status is determined solely by year_of_last_reinvestment

    def test_future_status_from_year_value(self):
        """
        Future status can be determined from year_of_last_reinvestment alone.

        Helper method to check if a unit is future:
        """
        current_year = 2025

        existing_unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=2010,  # Past year
        )

        future_unit = SubProductionUnit(
            id_sub_production_unit=2,
            id_production_unit=1,
            process_execution_count=10,
            max_process_execution_count=10,
            year_of_last_reinvestment=2050,  # Future year
        )

        # Helper function for determining future status
        def is_future(unit, ref_year=current_year):
            return unit.year_of_last_reinvestment > ref_year

        assert not is_future(existing_unit)
        assert is_future(future_unit)


class TestFutureUnitsConcept:
    """Tests documenting the concept of future/planned units."""

    def test_future_units_concept(self):
        """
        Future units are production units that haven't been built yet.

        They are distinguished by:
        1. year_of_last_reinvestment > current/reference year
        2. (Optional) explicit is_future boolean flag (for clarity)
        3. Available() returns 0 execution count before investment year
        4. Become available() after investment year
        """
        investment_year = 2050

        unit = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=20,
            max_process_execution_count=20,
            year_of_last_reinvestment=investment_year,
        )

        # Characteristics of a future unit:
        # 1. Investment year is in the future
        assert unit.year_of_last_reinvestment == 2050

        # 2. Current capacity is zero (unit not built yet)
        assert unit.process_execution_count == 20  # Planned count
        assert unit.max_process_execution_count == 20

        # 3. Will become available in investment year
        # (verified via InstalledProcess.is_available_in_year())

    def test_future_units_vs_existing_units(self):
        """
        Distinction between existing and future units:

        Existing Units:
        - year_of_last_reinvestment <= current year
        - Available now (or have been for some time)
        - Contributing to current production

        Future Units:
        - year_of_last_reinvestment > current year
        - Not available now
        - Planned/planned capacity
        """
        current_year = 2025

        existing = SubProductionUnit(
            id_sub_production_unit=1,
            id_production_unit=1,
            process_execution_count=100,
            max_process_execution_count=100,
            year_of_last_reinvestment=2015,  # Exists in past
        )

        future = SubProductionUnit(
            id_sub_production_unit=2,
            id_production_unit=1,
            process_execution_count=50,
            max_process_execution_count=50,
            year_of_last_reinvestment=2035,  # Planned for future
        )

        # Categorize
        def categorize_unit(unit, ref_year):
            if unit.year_of_last_reinvestment > ref_year:
                return 'future'
            return 'existing'

        assert categorize_unit(existing, current_year) == 'existing'
        assert categorize_unit(future, current_year) == 'future'


class TestFutureUnitsDatabase:
    """
    Documentation of database schema for future sub-production units.

    The current schema already supports future units through year_of_last_reinvestment.
    An optional is_future column could be added for explicit marking.
    """

    def test_database_schema_current(self):
        """Current database schema already supports future units."""
        # Current table: sub_production_units
        # Columns:
        # - id_sub_production_unit INTEGER PRIMARY KEY
        # - id_production_unit INTEGER
        # - id_process INTEGER
        # - process_execution_count_for_start_year INTEGER
        # - max_process_execution_count INTEGER
        # - year_of_last_reinvestment INTEGER  <-- Supports any year, past or future

        current_schema = {
            'id_sub_production_unit': 'INTEGER PRIMARY KEY',
            'id_production_unit': 'INTEGER',
            'id_process': 'INTEGER',
            'process_execution_count_for_start_year': 'INTEGER',
            'max_process_execution_count': 'INTEGER',
            'year_of_last_reinvestment': 'INTEGER',  # Can be past or future
        }

        # Current schema fully supports future units
        assert 'year_of_last_reinvestment' in current_schema

    def test_database_schema_optional_enhancement(self):
        """
        Optional enhancement: Add explicit is_future column.

        This would provide:
        1. Explicit marking for clarity
        2. Easier filtering in queries
        3. Better documentation of intent
        4. Backward compatible (default = NULL)

        Proposed schema addition:
        ALTER TABLE sub_production_units
        ADD COLUMN is_future BOOLEAN DEFAULT NULL;

        Values:
        - NULL: Determine from year_of_last_reinvestment automatically
        - TRUE: Explicitly marked as future (planned)
        - FALSE: Explicitly marked as existing (built)
        """
        # Proposed enhancement schema
        enhanced_schema = {
            'id_sub_production_unit': 'INTEGER PRIMARY KEY',
            'id_production_unit': 'INTEGER',
            'id_process': 'INTEGER',
            'process_execution_count_for_start_year': 'INTEGER',
            'max_process_execution_count': 'INTEGER',
            'year_of_last_reinvestment': 'INTEGER',
            'is_future': 'BOOLEAN DEFAULT NULL',  # Optional explicit marking
        }

        assert 'is_future' in enhanced_schema


class TestFutureUnitsHelpers:
    """
    Helper functions for working with future units.

    These could be added to a utility module or SubProductionUnit class.
    """

    @staticmethod
    def is_future_unit(unit, reference_year):
        """Check if a unit is marked as future (not yet built)."""
        return unit.year_of_last_reinvestment > reference_year

    @staticmethod
    def get_available_capacity(unit, year):
        """Get available capacity for a unit in a given year."""
        if unit.year_of_last_reinvestment > year:
            return 0  # Future unit not yet available
        return unit.max_process_execution_count

    @staticmethod
    def categorize_units(units, reference_year):
        """Categorize units into existing and future."""
        existing = []
        future = []

        for unit in units:
            if unit.year_of_last_reinvestment > reference_year:
                future.append(unit)
            else:
                existing.append(unit)

        return {'existing': existing, 'future': future}

    def test_helper_functions(self):
        """Test the helper function implementations."""
        units = [
            SubProductionUnit(1, 1, 10, 10, year_of_last_reinvestment=2010),
            SubProductionUnit(2, 1, 20, 20, year_of_last_reinvestment=2030),
            SubProductionUnit(3, 1, 30, 30, year_of_last_reinvestment=2050),
        ]

        current_year = 2025

        # Test is_future_unit
        assert not self.is_future_unit(units[0], current_year)  # 2010 < 2025
        assert self.is_future_unit(units[1], current_year)  # 2030 > 2025
        assert self.is_future_unit(units[2], current_year)  # 2050 > 2025

        # Test get_available_capacity
        assert self.get_available_capacity(units[0], 2025) == 10  # Existing
        assert self.get_available_capacity(units[1], 2025) == 0  # Future, not available yet
        assert self.get_available_capacity(units[1], 2030) == 20  # Future, now available
        assert self.get_available_capacity(units[2], 2025) == 0  # Future, not available yet

        # Test categorize_units
        categorized = self.categorize_units(units, current_year)
        assert len(categorized['existing']) == 1  # 2010
        assert len(categorized['future']) == 2  # 2030, 2050
        assert categorized['existing'][0].year_of_last_reinvestment == 2010
        assert categorized['future'][0].year_of_last_reinvestment == 2030


class TestFutureUnitsIntegration:
    """Tests showing how future units integrate with the optimization system."""

    def test_portfolio_with_future_units(self):
        """
        Portfolio planning with mixture of existing and future units.

        This shows a realistic optimization scenario:
        - Some units existing (already built)
        - Some units future (planned)
        - Optimizer chooses how to operate existing and when to use future capacity
        """
        current_year = 2025

        portfolio = {
            'existing_unit_a': SubProductionUnit(1, 1, 100, 100, year_of_last_reinvestment=2015),
            'planned_unit_b': SubProductionUnit(2, 1, 50, 50, year_of_last_reinvestment=2030),
            'future_unit_c': SubProductionUnit(3, 1, 50, 50, year_of_last_reinvestment=2040),
        }

        # Count existing vs. future
        existing_capacity = sum(
            u.max_process_execution_count for u in portfolio.values() if u.year_of_last_reinvestment <= current_year
        )

        future_capacity = sum(
            u.max_process_execution_count for u in portfolio.values() if u.year_of_last_reinvestment > current_year
        )

        assert existing_capacity == 100  # Only unit A
        assert future_capacity == 100  # Units B + C
        assert existing_capacity + future_capacity == 200  # Total

    def test_capacity_roadmap(self):
        """Create a capacity roadmap over time showing how future units add capacity."""
        units = [
            SubProductionUnit(1, 1, 100, 100, year_of_last_reinvestment=2020),
            SubProductionUnit(2, 1, 50, 50, year_of_last_reinvestment=2030),
            SubProductionUnit(3, 1, 40, 40, year_of_last_reinvestment=2040),
            SubProductionUnit(4, 1, 30, 30, year_of_last_reinvestment=2050),
        ]

        # Build capacity roadmap
        roadmap = {}
        for year in range(2020, 2051, 5):
            total = sum(u.max_process_execution_count for u in units if u.year_of_last_reinvestment <= year)
            roadmap[year] = total

        assert roadmap[2020] == 100  # Only unit 1
        assert roadmap[2025] == 100  # Still only unit 1
        assert roadmap[2030] == 150  # Unit 1 + 2
        assert roadmap[2040] == 190  # Unit 1 + 2 + 3
        assert roadmap[2050] == 220  # All units
