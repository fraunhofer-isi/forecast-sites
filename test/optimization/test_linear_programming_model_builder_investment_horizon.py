# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Pins the investment horizon decision for the rolling linear programming objective.

Confirmed by the domain owner in `bd show forecast-sites-private-6zj.18`: the rolling
paths charge the **full** net CAPEX and deduct no salvage value. Salvage only accrues at
the end of a single global observation period, which only `REGION_MULTI_PERIOD` has.
Deducting it inside a rolling horizon would require the opposite entry as well, writing
down residual value when a plant closes early, which the rolling formulation does not
model. See also the "Investment horizon" section in src/AGENTS.md.
"""

import unittest
from unittest import mock

import pytest

from optimization.linear_programming_model_builder import LinearProgrammingModelBuilder

FULL_INVEST_COST_IN_EURO = 1_000_000.0


class ProcessWithUnreadableLifetime:
    """
    A process whose lifetime cannot be read.

    Any salvage or annuity correction would have to consult the lifetime to work out the
    unused remainder, so making the attribute explode proves the objective never does.
    """

    @property
    def lifetime_in_years(self):
        message = 'the rolling horizon objective must not consult the process lifetime'
        raise AssertionError(message)

    def invest_cost_in_euro_per_process_count(
        self,
        _current_year,
        _interest_rate,
        _simulation_options,
        _capex_factor=1.0,
    ):
        return FULL_INVEST_COST_IN_EURO


class TestInvestmentHorizon(unittest.TestCase):
    """The rolling objective charges the whole investment, undiscounted and unreduced."""

    @staticmethod
    def _builder_with(process):
        optimization = mock.MagicMock()
        process_option = mock.MagicMock()
        process_option.process = process
        optimization._process_options = [process_option]
        return LinearProgrammingModelBuilder(optimization)

    def test_full_investment_is_charged_without_any_salvage_deduction(self):
        """
        Should return the investment cost unchanged, however long the plant lives.

        A plant far outlived by its own lifetime is exactly the case where a salvage
        deduction would bite hardest, so if one were ever introduced this assertion
        would drop below the full amount.
        """
        builder = self._builder_with(ProcessWithUnreadableLifetime())
        simulation_options = {'start_year': 2020}

        result = builder._invest_process_cost_in_euro_per_process_count(2025, 0.05, simulation_options)

        assert result[0] == pytest.approx(FULL_INVEST_COST_IN_EURO)

    def test_investment_is_not_discounted_in_the_current_year(self):
        """
        Should not discount the investment term.

        The investment falls in `current_year`, which *is* the discount base, so the
        discount factor is one by construction. A high interest rate must therefore
        leave the coefficient untouched. Annual operating costs are discounted
        elsewhere, in `_objective_coefficients_for_process_options`.
        """
        builder = self._builder_with(ProcessWithUnreadableLifetime())
        simulation_options = {'start_year': 2020}

        result = builder._invest_process_cost_in_euro_per_process_count(2025, 0.5, simulation_options)

        assert result[0] == pytest.approx(FULL_INVEST_COST_IN_EURO)
