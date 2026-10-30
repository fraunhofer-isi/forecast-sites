# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import fixture, patch

from optimization.optimization_result import OptimizationResult


@fixture
@patch(OptimizationResult._validate_and_fix)
def sut():
    return OptimizationResult(
        'mocked_process_execution_counts',
        'mocked_carrier_amounts',
    )


def test_construction(sut):
    assert sut is not None


def test_processes(sut):
    sut.process_execution_counts = {'mocked_process': 1}
    result = sut.processes
    assert result == ['mocked_process']


def test_carriers(sut):
    sut.purchased_carrier_amounts = {'mocked_carrier': 1}
    result = sut.carriers
    assert result == ['mocked_carrier']


class TestValidateAndFix:
    def test_large_negative_process_execution_count_raises_error(self, sut):
        """Should raise ValueError for significantly negative values (optimizer bug)."""
        sut.process_execution_counts = {'mocked_process': -1}
        sut.purchased_carrier_amounts = {}

        with pytest.raises(ValueError, match='Process execution count must not be negative'):
            sut._validate_and_fix()

    def test_small_negative_process_execution_count_is_set_to_zero(self, sut):
        sut.process_execution_counts = {'mocked_process': -1e-10}
        sut.purchased_carrier_amounts = {}

        sut._validate_and_fix()

        assert sut.process_execution_counts['mocked_process'] == 0

    def test_negative_purchased_carrier_amount(self, sut):
        sut.process_execution_counts = {}
        sut.purchased_carrier_amounts = {'mocked_carrier': -1}
        with pytest.raises(ValueError, match='Purchased carrier amount must not be negative'):
            sut._validate_and_fix()


class TestCostPerYear:
    """Test cost per year calculation."""

    def test_cost_per_year_returns_none_when_missing_total_cost(self):
        """Should return None if total_cost_in_euro is None."""
        result = OptimizationResult(
            {'p1': 1},
            {'c1': 1},
            total_cost_in_euro=None,
            modeled_year_count=10,
            interest_rate=0.05,
        )
        assert result.cost_per_year_in_euro is None

    def test_cost_per_year_returns_none_when_missing_year_count(self):
        """Should return None if modeled_year_count is None."""
        result = OptimizationResult(
            {'p1': 1},
            {'c1': 1},
            total_cost_in_euro=1000,
            modeled_year_count=None,
            interest_rate=0.05,
        )
        assert result.cost_per_year_in_euro is None

    def test_cost_per_year_returns_none_when_missing_interest_rate(self):
        """Should return None if interest_rate is None."""
        result = OptimizationResult(
            {'p1': 1},
            {'c1': 1},
            total_cost_in_euro=1000,
            modeled_year_count=10,
            interest_rate=None,
        )
        assert result.cost_per_year_in_euro is None

    def test_cost_per_year_raises_error_for_zero_year_count(self):
        """Should raise ValueError if year count is 0."""
        with pytest.raises(ValueError, match='Modeled year count must be positive'):
            OptimizationResult(
                {'p1': 1},
                {'c1': 1},
                total_cost_in_euro=1000,
                modeled_year_count=0,
                interest_rate=0.05,
            )

    def test_cost_per_year_raises_error_for_negative_year_count(self):
        """Should raise ValueError if year count is negative."""
        with pytest.raises(ValueError, match='Modeled year count must be positive'):
            OptimizationResult(
                {'p1': 1},
                {'c1': 1},
                total_cost_in_euro=1000,
                modeled_year_count=-5,
                interest_rate=0.05,
            )

    def test_cost_per_year_with_zero_interest_rate(self):
        """Should divide total cost by year count when interest rate is 0."""
        result = OptimizationResult(
            {'p1': 1},
            {'c1': 1},
            total_cost_in_euro=1000,
            modeled_year_count=10,
            interest_rate=0,
        )
        assert result.cost_per_year_in_euro == 100  # 1000 / 10

    def test_cost_per_year_with_positive_interest_rate(self):
        """Should calculate annuity factor with positive interest rate."""
        result = OptimizationResult(
            {'p1': 1},
            {'c1': 1},
            total_cost_in_euro=10000,
            modeled_year_count=10,
            interest_rate=0.05,
        )
        # Cost per year should be positive and less than simple division for positive rate
        assert result.cost_per_year_in_euro is not None
        assert result.cost_per_year_in_euro > 0

    def test_normalized_total_cost_converts_to_float(self):
        """Should convert total cost to float."""
        result = OptimizationResult(
            {'p1': 1},
            {'c1': 1},
            total_cost_in_euro=5000,
            modeled_year_count=10,
            interest_rate=0.05,
        )
        assert isinstance(result.total_cost_in_euro, float)

    def test_normalized_interest_rate_converts_to_float(self):
        """Should convert interest rate to float."""
        result = OptimizationResult(
            {'p1': 1},
            {'c1': 1},
            total_cost_in_euro=1000,
            modeled_year_count=10,
            interest_rate=5,  # Integer input
        )
        assert isinstance(result.interest_rate, float)
        assert result.interest_rate == 5.0


class TestCarrierNettoAmounts:
    def test_defaults_to_empty_dict_when_not_provided(self):
        result = OptimizationResult({'p': 0}, {'c': 0.0})
        assert result.carrier_netto_amounts == {}

    def test_none_argument_becomes_empty_dict(self):
        result = OptimizationResult({'p': 0}, {'c': 0.0}, carrier_netto_amounts=None)
        assert result.carrier_netto_amounts == {}

    def test_stores_provided_carrier_netto_amounts(self):
        carrier = object()
        result = OptimizationResult({'p': 0}, {carrier: 0.0}, carrier_netto_amounts={carrier: 42.0})
        assert result.carrier_netto_amounts[carrier] == 42.0

    def test_carrier_netto_amounts_independent_of_purchased_amounts(self):
        """carrier_netto_amounts and purchased_carrier_amounts are separate fields."""
        carrier = object()
        result = OptimizationResult(
            {'p': 0},
            {carrier: 5.0},
            carrier_netto_amounts={carrier: -3.0},
        )
        assert result.purchased_carrier_amounts[carrier] == 5.0
        assert result.carrier_netto_amounts[carrier] == -3.0
