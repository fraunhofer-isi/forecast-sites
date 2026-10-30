# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Financial calculations for processes.

This module encapsulates cost and financial computations,
separating financial logic from core process behavior.
"""


class ProcessFinancialCalculator:
    """
    Calculator for process financial metrics.

    Handles annuity factors, compound factors, and financial
    cost calculations specific to process economics.
    """

    def __init__(self, depreciation_period: int):
        """
        Initialize calculator with depreciation period.

        Args:
            depreciation_period: Accounting depreciation period in years (must be > 0).

        Raises:
            ValueError: If depreciation_period <= 0.

        """
        if depreciation_period <= 0:
            msg = 'Depreciation period must be > 0'
            raise ValueError(msg)
        self._depreciation_period = depreciation_period

    def compound_factor(self, interest_rate: float) -> float:
        """
        Calculate compound growth factor.

        Computes (1 + interest_rate) ^ depreciation_period,
        used in annuity calculations.

        Args:
            interest_rate: Annual interest/discount rate (e.g., 0.05 for 5%).

        Returns:
            Compound factor: (1 + interest_rate) ^ depreciation_period.

        """
        return (1 + interest_rate) ** self._depreciation_period

    def annuity_factor(self, interest_rate: float) -> float:
        """
        Calculate annuity factor for levelized cost calculations.

        Converts lump-sum investment cost to equivalent annual payment,
        accounting for time value of money and process lifetime.

        Formula: (r * CF) / (CF - 1), where CF = compound_factor

        Args:
            interest_rate: Annual interest/discount rate.

        Returns:
            Annuity factor for cost levelization.

        Raises:
            ValueError: If interest_rate produces division by zero (rare edge case).

        """
        compound = self.compound_factor(interest_rate)

        # Avoid division by zero if compound factor is 1
        # (happens when interest_rate = 0 and depreciation_period = 0, already caught in __init__)
        if compound == 1:
            msg = 'Cannot calculate annuity factor when compound factor = 1'
            raise ValueError(msg)

        return interest_rate * compound / (compound - 1)

    @staticmethod
    def net_investment(capex: float, funding: float, capex_factor: float = 1.0) -> float:
        """
        Calculate the investment the investor actually has to pay.

        The capex_factor scales the CAPEX *before* the investment funding is deducted.
        That ordering is load bearing: the start year factor is a calibration penalty
        against unrealistic technology switching, so a fully funded process must still
        be penalized. Deducting the funding first would yield zero for a fully funded
        process and silently disable the penalty.

        The result is floored at zero, so funding exceeding the scaled CAPEX never
        turns an investment into a gain. That flooring is not a defensive guard
        against bad input -- it *is* the mechanism that enforces "funding never
        exceeds CAPEX". Deliberately no input validation; see
        `bd show forecast-sites-private-6zj.19`.

        Args:
            capex: Gross capital expenditure.
            funding: Investment funding (CAPEX support) granted for the investment.
            capex_factor: Scaling factor applied to the CAPEX before deducting funding.

        Returns:
            max(capex * capex_factor - funding, 0.0)

        """
        return max(capex * capex_factor - funding, 0.0)
