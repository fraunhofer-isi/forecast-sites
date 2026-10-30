# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from interpolation.interpolation_data import InterpolationData


class TestInterpolationData:
    """Test cases for InterpolationData value object."""

    def test_interpolation_data_stores_start_year_value(self):
        """Test that start year value is stored correctly."""
        data = InterpolationData(value_for_start_year=100.0, value_for_end_year=200.0)
        assert data.value_for_start_year == 100.0

    def test_interpolation_data_stores_end_year_value(self):
        """Test that end year value is stored correctly."""
        data = InterpolationData(value_for_start_year=100.0, value_for_end_year=200.0)
        assert data.value_for_end_year == 200.0

    def test_interpolation_data_stores_interim_year_value(self):
        """Test that interim year value is stored when provided."""
        data = InterpolationData(value_for_start_year=100.0, value_for_end_year=200.0, value_for_interim_year=150.0)
        assert data.value_for_interim_year == 150.0

    def test_interpolation_data_interim_year_is_none_by_default(self):
        """Test that interim year value defaults to None."""
        data = InterpolationData(value_for_start_year=100.0, value_for_end_year=200.0)
        assert data.value_for_interim_year is None

    def test_interpolation_data_with_negative_values(self):
        """Test InterpolationData with negative values."""
        data = InterpolationData(value_for_start_year=-50.0, value_for_end_year=50.0, value_for_interim_year=0.0)
        assert data.value_for_start_year == -50.0
        assert data.value_for_end_year == 50.0
        assert data.value_for_interim_year == 0.0

    def test_interpolation_data_with_zero_values(self):
        """Test InterpolationData with zero values."""
        data = InterpolationData(value_for_start_year=0.0, value_for_end_year=0.0)
        assert data.value_for_start_year == 0.0
        assert data.value_for_end_year == 0.0
