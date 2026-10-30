# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

from utils.time_utils import _add_year_prefix, create_time_span, to_year_strings


class TestCreateTimeSpan:
    """Tests for create_time_span function."""

    def test_create_time_span_single_year(self) -> None:
        """create_time_span with start_year == end_year returns single year."""
        result = create_time_span(2020, 2020)

        assert result == [2020]

    def test_create_time_span_simple_range(self) -> None:
        """create_time_span creates range from start to end."""
        result = create_time_span(2020, 2025)

        assert result == [2020, 2021, 2022, 2023, 2024, 2025]

    def test_create_time_span_with_increment_2(self) -> None:
        """create_time_span with increment=2 creates every other year."""
        result = create_time_span(2020, 2030, year_increment=2)

        assert result == [2020, 2022, 2024, 2026, 2028, 2030]

    def test_create_time_span_with_increment_5(self) -> None:
        """create_time_span with increment=5 creates every 5th year."""
        result = create_time_span(2000, 2020, year_increment=5)

        assert result == [2000, 2005, 2010, 2015, 2020]

    def test_create_time_span_with_increment_10(self) -> None:
        """create_time_span with increment=10 creates every 10th year."""
        result = create_time_span(2010, 2050, year_increment=10)

        assert result == [2010, 2020, 2030, 2040, 2050]

    def test_create_time_span_end_year_included_when_not_divisible(self) -> None:
        """create_time_span ensures end_year is included even if not divisible by increment."""
        result = create_time_span(2020, 2025, year_increment=3)

        # Should be [2020, 2023, 2025] because 2026 would exceed end_year
        assert 2025 in result
        assert result[-1] == 2025

    def test_create_time_span_end_year_included_when_perfectly_divisible(self) -> None:
        """create_time_span includes end_year when perfectly divisible by increment."""
        result = create_time_span(2020, 2030, year_increment=2)

        assert result[-1] == 2030
        assert result == [2020, 2022, 2024, 2026, 2028, 2030]

    def test_create_time_span_with_increment_larger_than_range(self) -> None:
        """create_time_span when increment is larger than range still includes end_year."""
        result = create_time_span(2020, 2025, year_increment=10)

        assert result == [2020, 2025]

    def test_create_time_span_with_large_increment(self) -> None:
        """create_time_span with very large increment still includes end_year."""
        result = create_time_span(2020, 2025, year_increment=100)

        assert result == [2020, 2025]

    def test_create_time_span_default_increment_is_1(self) -> None:
        """create_time_span default increment is 1."""
        result = create_time_span(2020, 2023)

        assert result == [2020, 2021, 2022, 2023]

    def test_create_time_span_with_negative_years(self) -> None:
        """create_time_span works with negative years."""
        result = create_time_span(-2000, -1990, year_increment=5)

        assert -2000 in result
        assert -1990 in result

    def test_create_time_span_with_zero(self) -> None:
        """create_time_span works with zero as year."""
        result = create_time_span(0, 5)

        assert result == [0, 1, 2, 3, 4, 5]

    def test_create_time_span_crossing_zero(self) -> None:
        """create_time_span works with ranges crossing zero."""
        result = create_time_span(-2, 2)

        assert result == [-2, -1, 0, 1, 2]

    def test_create_time_span_returns_list(self) -> None:
        """create_time_span returns a list."""
        result = create_time_span(2020, 2022)

        assert isinstance(result, list)

    def test_create_time_span_is_sorted(self) -> None:
        """create_time_span returns sorted list."""
        result = create_time_span(2020, 2030, year_increment=3)

        assert result == sorted(result)

    def test_create_time_span_no_duplicates(self) -> None:
        """create_time_span returns no duplicate years."""
        result = create_time_span(2020, 2030, year_increment=2)

        assert len(result) == len(set(result))

    def test_create_time_span_large_range(self) -> None:
        """create_time_span handles large year ranges."""
        result = create_time_span(1000, 3000, year_increment=100)

        assert result[0] == 1000
        assert result[-1] == 3000

    def test_create_time_span_contains_all_expected_years(self) -> None:
        """create_time_span contains all years in the range."""
        result = create_time_span(2020, 2023, year_increment=1)

        assert all(year in result for year in [2020, 2021, 2022, 2023])

    def test_create_time_span_increment_3_from_2020_to_2025(self) -> None:
        """create_time_span with increment=3 from 2020 to 2025."""
        result = create_time_span(2020, 2025, year_increment=3)

        assert 2020 in result
        assert 2025 in result
        # After 2020, adding 3 gives 2023, then 2026 which exceeds 2025
        # So 2025 is appended separately
        assert result == [2020, 2023, 2025]


class TestToYearStrings:
    """Tests for to_year_strings function."""

    def test_to_year_strings_single_year(self) -> None:
        """to_year_strings converts single year to Y-prefixed string."""
        result = to_year_strings([2020])

        assert result == ['Y2020']

    def test_to_year_strings_multiple_years(self) -> None:
        """to_year_strings converts multiple years to Y-prefixed strings."""
        result = to_year_strings([2020, 2021, 2022])

        assert result == ['Y2020', 'Y2021', 'Y2022']

    def test_to_year_strings_empty_list(self) -> None:
        """to_year_strings handles empty list."""
        result = to_year_strings([])

        assert result == []

    def test_to_year_strings_with_gaps(self) -> None:
        """to_year_strings preserves gaps in year list."""
        result = to_year_strings([2020, 2022, 2025])

        assert result == ['Y2020', 'Y2022', 'Y2025']

    def test_to_year_strings_with_negative_years(self) -> None:
        """to_year_strings handles negative years."""
        result = to_year_strings([-1, 0, 1])

        assert result == ['Y-1', 'Y0', 'Y1']

    def test_to_year_strings_returns_list(self) -> None:
        """to_year_strings returns a list."""
        result = to_year_strings([2020])

        assert isinstance(result, list)

    def test_to_year_strings_all_strings(self) -> None:
        """to_year_strings returns all string elements."""
        result = to_year_strings([2020, 2021, 2022])

        assert all(isinstance(year_str, str) for year_str in result)

    def test_to_year_strings_preserves_order(self) -> None:
        """to_year_strings preserves order of input years."""
        result = to_year_strings([2025, 2020, 2023])

        assert result == ['Y2025', 'Y2020', 'Y2023']

    def test_to_year_strings_large_years(self) -> None:
        """to_year_strings handles large year values."""
        result = to_year_strings([1000, 5000, 9999])

        assert result == ['Y1000', 'Y5000', 'Y9999']

    def test_to_year_strings_with_duplicates(self) -> None:
        """to_year_strings preserves duplicates from input."""
        result = to_year_strings([2020, 2020, 2021])

        assert result == ['Y2020', 'Y2020', 'Y2021']

    def test_to_year_strings_zero(self) -> None:
        """to_year_strings handles zero."""
        result = to_year_strings([0])

        assert result == ['Y0']

    def test_to_year_strings_integration_with_create_time_span(self) -> None:
        """to_year_strings works with output of create_time_span."""
        time_span = create_time_span(2020, 2023)
        result = to_year_strings(time_span)

        assert result == ['Y2020', 'Y2021', 'Y2022', 'Y2023']


class TestAddYearPrefix:
    """Tests for _add_year_prefix function."""

    def test_add_year_prefix_to_year(self) -> None:
        """_add_year_prefix adds 'Y' prefix to year."""
        result = _add_year_prefix(2020)

        assert result == 'Y2020'

    def test_add_year_prefix_converts_to_string(self) -> None:
        """_add_year_prefix converts year to string with prefix."""
        result = _add_year_prefix(2021)

        assert isinstance(result, str)
        assert result == 'Y2021'

    def test_add_year_prefix_zero(self) -> None:
        """_add_year_prefix adds prefix to zero."""
        result = _add_year_prefix(0)

        assert result == 'Y0'

    def test_add_year_prefix_negative_year(self) -> None:
        """_add_year_prefix adds prefix to negative year."""
        result = _add_year_prefix(-100)

        assert result == 'Y-100'

    def test_add_year_prefix_large_year(self) -> None:
        """_add_year_prefix handles large years."""
        result = _add_year_prefix(9999)

        assert result == 'Y9999'

    def test_add_year_prefix_year_as_string(self) -> None:
        """_add_year_prefix converts string year to Y-prefixed string."""
        result = _add_year_prefix('2020')

        assert result == 'Y2020'

    def test_add_year_prefix_year_with_float(self) -> None:
        """_add_year_prefix converts float year to Y-prefixed string."""
        result = _add_year_prefix(2020.5)

        assert result == 'Y2020.5'


class TestTimeUtilsIntegration:
    """Integration tests for time_utils module."""

    def test_create_and_convert_time_span(self) -> None:
        """Integration: create_time_span and to_year_strings workflow."""
        time_span = create_time_span(2020, 2025, year_increment=2)
        year_strings = to_year_strings(time_span)

        assert year_strings == ['Y2020', 'Y2022', 'Y2024', 'Y2025']

    def test_full_workflow_with_different_increments(self) -> None:
        """Full workflow with various increment values."""
        for increment in [1, 2, 5, 10]:
            time_span = create_time_span(2000, 2050, year_increment=increment)
            year_strings = to_year_strings(time_span)

            # All years should be included
            assert 2000 in time_span
            assert 2050 in time_span
            # All strings should start with 'Y'
            assert all(ys.startswith('Y') for ys in year_strings)

    def test_typical_use_case_annual_years(self) -> None:
        """Typical use case: annual years from 2020-2030."""
        time_span = create_time_span(2020, 2030)
        year_strings = to_year_strings(time_span)

        assert len(year_strings) == 11  # 2020-2030 inclusive
        assert year_strings[0] == 'Y2020'
        assert year_strings[-1] == 'Y2030'

    def test_typical_use_case_5_year_intervals(self) -> None:
        """Typical use case: 5-year intervals from 2010-2050."""
        time_span = create_time_span(2010, 2050, year_increment=5)
        year_strings = to_year_strings(time_span)

        expected = ['Y2010', 'Y2015', 'Y2020', 'Y2025', 'Y2030', 'Y2035', 'Y2040', 'Y2045', 'Y2050']
        assert year_strings == expected

    def test_historical_and_future_years(self) -> None:
        """Works with historical (past) and future years."""
        time_span = create_time_span(1980, 2050, year_increment=10)

        assert 1980 in time_span
        assert 2050 in time_span
        assert len(time_span) > 0
