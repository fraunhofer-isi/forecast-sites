# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest
from test_utils.isi_mock import patch

from interpolation.interpolator import (
    exponential_decrease,
    interpolate,
    interpolate_cost,
    logging,
)


class TestInterpolate:
    """Test the linear interpolate function."""

    @pytest.fixture
    def simulation_options(self):
        """Standard simulation options."""
        return {'start_year': 2020, 'interim_year': 2025, 'end_year': 2030}

    @pytest.fixture
    def interpolation_data_no_interim(self):
        """Interpolation data without interim year."""
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_end_year = 200
        data.value_for_interim_year = None
        return data

    @pytest.fixture
    def interpolation_data_with_interim(self):
        """Interpolation data with interim year."""
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_interim_year = 150
        data.value_for_end_year = 200
        return data

    def test_interpolate_start_year(self, simulation_options, interpolation_data_no_interim):
        """Should return start value at start year."""
        value = interpolate(2020, simulation_options, interpolation_data_no_interim)
        assert value == pytest.approx(100)

    def test_interpolate_end_year(self, simulation_options, interpolation_data_no_interim):
        """Should return end value at end year."""
        value = interpolate(2030, simulation_options, interpolation_data_no_interim)
        assert value == pytest.approx(200)

    def test_interpolate_middle_year(self, simulation_options, interpolation_data_no_interim):
        """Should interpolate correctly at middle year."""
        # At year 2025 (midpoint): value should be 150
        value = interpolate(2025, simulation_options, interpolation_data_no_interim)
        assert value == pytest.approx(150)

    def test_interpolate_with_interim_before_interim_year(self, simulation_options, interpolation_data_with_interim):
        """Should use first segment before interim year."""
        # Between 2020 and 2025: slope = (150-100)/(2025-2020) = 10
        # At 2022: 100 + 10*(2022-2020) = 120
        value = interpolate(2022, simulation_options, interpolation_data_with_interim)
        assert value == pytest.approx(120)

    def test_interpolate_with_interim_after_interim_year(self, simulation_options, interpolation_data_with_interim):
        """Should use second segment after interim year."""
        # Between 2025 and 2030: slope = (200-150)/(2030-2025) = 10
        # At 2027: 150 + 10*(2027-2025) = 170
        value = interpolate(2027, simulation_options, interpolation_data_with_interim)
        assert value == pytest.approx(170)

    def test_interpolate_at_interim_year(self, simulation_options, interpolation_data_with_interim):
        """Should return interim value at interim year."""
        value = interpolate(2025, simulation_options, interpolation_data_with_interim)
        assert value == pytest.approx(150)

    def test_interpolate_negative_values(self, simulation_options):
        """Should handle negative values."""
        data = Mock()
        data.value_for_start_year = -100
        data.value_for_end_year = 100
        data.value_for_interim_year = None

        value = interpolate(2025, simulation_options, data)
        assert value == pytest.approx(0)


class TestInterpolateCost:
    """Test the linear interpolate_cost function."""

    @pytest.fixture
    def simulation_options(self):
        """Standard simulation options."""
        return {'start_year': 2020, 'interim_year': 2025, 'end_year': 2030}

    @pytest.fixture
    def interpolation_data(self):
        """Interpolation data with interim value."""
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_interim_year = 150
        data.value_for_end_year = 200
        return data

    def test_requires_interim_value(self, simulation_options):
        """Should raise ValueError if interim value is None."""
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_interim_year = None
        data.value_for_end_year = 200

        with pytest.raises(ValueError, match='interim_value must be provided'):
            interpolate_cost(2025, simulation_options, data)

    def test_cost_interpolate_start_year(self, simulation_options, interpolation_data):
        """Should return start value at start year."""
        value = interpolate_cost(2020, simulation_options, interpolation_data)
        assert value == pytest.approx(100)

    def test_cost_interpolate_interim_year(self, simulation_options, interpolation_data):
        """Should return interim value at interim year."""
        value = interpolate_cost(2025, simulation_options, interpolation_data)
        assert value == pytest.approx(150)

    def test_cost_interpolate_end_year(self, simulation_options, interpolation_data):
        """Should return end value at end year."""
        value = interpolate_cost(2030, simulation_options, interpolation_data)
        assert value == pytest.approx(200)

    def test_cost_interpolate_before_interim(self, simulation_options, interpolation_data):
        """Should interpolate correctly before interim year."""
        # Between 2020 and 2025: slope = (150-100)/(2025-2020) = 10
        # At 2022: 100 + 10*2 = 120
        value = interpolate_cost(2022, simulation_options, interpolation_data)
        assert value == pytest.approx(120)

    def test_cost_interpolate_after_interim(self, simulation_options, interpolation_data):
        """Should interpolate correctly after interim year."""
        # Between 2025 and 2030: slope = (200-150)/(2030-2025) = 10
        # At 2027: 150 + 10*2 = 170
        value = interpolate_cost(2027, simulation_options, interpolation_data)
        assert value == pytest.approx(170)

    @patch(logging.warning)
    def test_warns_when_interim_exceeds_end_value(self, simulation_options):
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_interim_year = 250
        data.value_for_end_year = 200

        interpolate_cost(2025, simulation_options, data)

        assert logging.warning.called


class TestExponentialDecrease:
    """Test the exponential decrease function."""

    @pytest.fixture
    def simulation_options(self):
        """Standard simulation options."""
        return {'start_year': 2020, 'interim_year': 2025, 'end_year': 2030}

    @pytest.fixture
    def interpolation_data(self):
        """Interpolation data with interim value."""
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_interim_year = 50
        data.value_for_end_year = 0
        return data

    def test_exponential_start_year(self, simulation_options, interpolation_data):
        """Should return start value at start year."""
        value = exponential_decrease(2020, simulation_options, interpolation_data)
        assert value == pytest.approx(100)

    def test_exponential_interim_year(self, simulation_options, interpolation_data):
        """Should return interim value at interim year."""
        value = exponential_decrease(2025, simulation_options, interpolation_data)
        assert value == pytest.approx(50)

    def test_exponential_before_interim(self, simulation_options, interpolation_data):
        """Should use exponential decay before interim year."""
        # Start: 100, Interim: 50
        # At 2020: 100
        # At 2025: 50
        # Slope factor = (50/100)^(1/5) ≈ 0.87055
        value = exponential_decrease(2022, simulation_options, interpolation_data)
        # At 2022 (year 2): 100 * 0.87055^2 ≈ 75.8
        assert 70 < value < 80  # Rough check for exponential decay

    def test_exponential_requires_interim(self, simulation_options):
        """Should raise ValueError if interim value is None."""
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_interim_year = None
        data.value_for_end_year = 200

        with pytest.raises(ValueError, match='interim_value must be provided'):
            exponential_decrease(2025, simulation_options, data)

    def test_exponential_with_increasing_values(self, simulation_options):
        """Should handle case where values increase then decrease."""
        data = Mock()
        data.value_for_start_year = 100
        data.value_for_interim_year = 200
        data.value_for_end_year = 50

        value_interim = exponential_decrease(2025, simulation_options, data)
        assert value_interim == pytest.approx(200)

        value_end = exponential_decrease(2030, simulation_options, data)
        assert value_end == pytest.approx(50)
