# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for LinearProgrammingModelBuilder objective coefficient capex factor."""

import unittest
from unittest import mock

import pytest

from optimization.linear_programming_model_builder import LinearProgrammingModelBuilder
from processes.installed_process import InstalledProcess


def _builder_with_process(process):
    mock_optimization = mock.MagicMock()
    mock_process_option = mock.MagicMock()
    mock_process_option.process = process
    mock_optimization._process_options = [mock_process_option]
    return LinearProgrammingModelBuilder(mock_optimization)


class TestObjectiveCoefficientCapexFactor(unittest.TestCase):
    """
    Test that the start year capex factor is handed to the process.

    The builder never scales the cost itself: the factor has to be applied to the
    CAPEX before the investment funding is deducted, which only the process can do.
    """

    def test_capex_factor_is_handed_to_process_in_start_year(self):
        """Should pass the configured factor to the process in the start year."""
        process = mock.MagicMock()
        process.invest_cost_in_euro_per_process_count.return_value = 100.0
        builder = _builder_with_process(process)

        simulation_options = {
            'start_year': 2020,
            'start_year_capex_factor': 0.5,
        }

        result = builder._invest_process_cost_in_euro_per_process_count(2020, 0.05, simulation_options)

        process.invest_cost_in_euro_per_process_count.assert_called_once_with(
            2020,
            0.05,
            simulation_options,
            0.5,
        )
        # The process applies the factor internally, so the builder returns its result unchanged.
        assert result[0] == pytest.approx(100.0, abs=0.1)

    def test_capex_factor_is_neutral_after_start_year(self):
        """Should pass a neutral factor of 1.0 outside the start year."""
        process = mock.MagicMock()
        process.invest_cost_in_euro_per_process_count.return_value = 100.0
        builder = _builder_with_process(process)

        simulation_options = {
            'start_year': 2020,
            'start_year_capex_factor': 0.5,
        }

        builder._invest_process_cost_in_euro_per_process_count(2025, 0.05, simulation_options)

        process.invest_cost_in_euro_per_process_count.assert_called_once_with(
            2025,
            0.05,
            simulation_options,
            1.0,
        )

    def test_installed_process_ignores_the_capex_factor(self):
        """Should leave an installed process unscaled, because it ignores the factor itself."""
        process = mock.MagicMock(spec=InstalledProcess)
        process.invest_cost_in_euro_per_process_count.return_value = 100.0
        builder = _builder_with_process(process)

        simulation_options = {
            'start_year': 2020,
            'start_year_capex_factor': 0.5,
        }

        result = builder._invest_process_cost_in_euro_per_process_count(2020, 0.05, simulation_options)

        assert result[0] == pytest.approx(100.0, abs=0.1)
