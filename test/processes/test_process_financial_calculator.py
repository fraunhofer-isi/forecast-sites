# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from processes.process_financial_calculator import ProcessFinancialCalculator


class TestProcessFinancialCalculatorInit:
    """Test ProcessFinancialCalculator initialization."""

    def test_init_valid_depreciation_period(self):
        """Test initialization with valid depreciation period."""
        calc = ProcessFinancialCalculator(10)
        assert calc._depreciation_period == 10

    def test_init_zero_depreciation_period_raises(self):
        """Test initialization with zero depreciation period raises ValueError."""
        with pytest.raises(ValueError, match='Depreciation period must be > 0'):
            ProcessFinancialCalculator(0)

    def test_init_negative_depreciation_period_raises(self):
        """Test initialization with negative depreciation period raises ValueError."""
        with pytest.raises(ValueError, match='Depreciation period must be > 0'):
            ProcessFinancialCalculator(-5)

    def test_init_one_year_period(self):
        """Test initialization with 1-year depreciation period."""
        calc = ProcessFinancialCalculator(1)
        assert calc._depreciation_period == 1


class TestCompoundFactor:
    """Test compound factor calculations."""

    def test_compound_factor_zero_interest(self):
        """Test compound factor with zero interest rate."""
        calc = ProcessFinancialCalculator(5)
        result = calc.compound_factor(0.0)
        assert result == 1.0

    def test_compound_factor_positive_interest(self):
        """Test compound factor with positive interest rate."""
        calc = ProcessFinancialCalculator(2)
        result = calc.compound_factor(0.05)
        # (1.05)^2 = 1.1025
        assert abs(result - 1.1025) < 1e-6

    def test_compound_factor_high_interest(self):
        """Test compound factor with high interest rate."""
        calc = ProcessFinancialCalculator(10)
        result = calc.compound_factor(0.10)
        # (1.10)^10
        assert result > 1.0
        assert abs(result - 2.5937424601) < 1e-6

    def test_compound_factor_one_year(self):
        """Test compound factor with 1-year depreciation period."""
        calc = ProcessFinancialCalculator(1)
        result = calc.compound_factor(0.05)
        assert abs(result - 1.05) < 1e-6


class TestAnnuityFactor:
    """Test annuity factor calculations."""

    def test_annuity_factor_positive_interest(self):
        """Test annuity factor with positive interest rate."""
        calc = ProcessFinancialCalculator(10)
        result = calc.annuity_factor(0.05)
        # Should be positive
        assert result > 0
        # Annuity factor for 10 years at 5% is approximately 0.1295
        assert 0.12 < result < 0.14

    def test_annuity_factor_high_interest(self):
        """Test annuity factor with high interest rate."""
        calc = ProcessFinancialCalculator(5)
        result = calc.annuity_factor(0.10)
        assert result > 0

    def test_annuity_factor_low_interest(self):
        """Test annuity factor with low interest rate."""
        calc = ProcessFinancialCalculator(20)
        result = calc.annuity_factor(0.01)
        assert result > 0

    def test_annuity_factor_zero_interest_raises(self):
        """Test annuity factor with zero interest raises error."""
        calc = ProcessFinancialCalculator(1)
        with pytest.raises(ValueError, match='Cannot calculate annuity factor'):
            calc.annuity_factor(0.0)

    def test_annuity_factor_negative_interest_valid(self):
        """Test annuity factor with negative interest rate (valid in theory)."""
        calc = ProcessFinancialCalculator(10)
        # Negative interest is mathematically valid
        result = calc.annuity_factor(-0.02)
        # Should calculate without error
        assert isinstance(result, float)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_short_depreciation_period(self):
        """Test with 1-year depreciation period."""
        calc = ProcessFinancialCalculator(1)
        result = calc.compound_factor(0.05)
        assert abs(result - 1.05) < 1e-6

    def test_very_long_depreciation_period(self):
        """Test with very long depreciation period."""
        calc = ProcessFinancialCalculator(100)
        result = calc.compound_factor(0.01)
        # (1.01)^100 ≈ 2.7048
        assert 2.7 < result < 2.71

    def test_annuity_factor_convergence(self):
        """Test annuity factor approaches 1/depreciation_period for small interest."""
        calc = ProcessFinancialCalculator(10)
        # With very small interest rate, annuity factor should approach 1/10
        result = calc.annuity_factor(0.001)
        assert 0.09 < result < 0.11

    def test_compound_factor_symmetry(self):
        """Test compound factor calculation consistency."""
        calc1 = ProcessFinancialCalculator(5)
        calc2 = ProcessFinancialCalculator(5)

        interest_rate = 0.05
        result1 = calc1.compound_factor(interest_rate)
        result2 = calc2.compound_factor(interest_rate)

        assert result1 == result2


class TestNetInvestment:
    """Test the net investment calculation (CAPEX support)."""

    def test_funding_is_deducted_from_capex(self):
        """Should deduct the investment funding from the CAPEX."""
        assert ProcessFinancialCalculator.net_investment(1000.0, 300.0) == pytest.approx(700.0)

    def test_default_factor_leaves_capex_unscaled(self):
        """Should treat a missing factor as 1.0."""
        assert ProcessFinancialCalculator.net_investment(1000.0, 0.0) == pytest.approx(1000.0)

    def test_factor_is_applied_before_funding_is_deducted(self):
        """
        Should scale the CAPEX first, so a fully funded process stays penalized.

        Deliberate modeling decision, confirmed by the domain owner in
        `bd show forecast-sites-private-6zj.18`. The start year factor is a calibration
        penalty against unrealistic technology switching; deducting the funding first
        would collapse a fully funded process to zero and silently disable the penalty.
        """
        result = ProcessFinancialCalculator.net_investment(1000.0, 1000.0, 5.0)

        # 1000 * 5 - 1000 = 4000; deducting first would collapse to 0
        assert result == pytest.approx(4000.0)

    def test_result_is_never_negative(self):
        """
        Should floor the result at zero when funding exceeds the scaled CAPEX.

        The flooring is not a defensive guard against bad input -- it *is* the mechanism
        that enforces "funding never exceeds CAPEX". Input validation was considered and
        deliberately rejected, see `bd show forecast-sites-private-6zj.19`.
        """
        assert ProcessFinancialCalculator.net_investment(1000.0, 1500.0) == 0.0
