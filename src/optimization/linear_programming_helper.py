# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from utils.time_utils import create_time_span


class LinearProgrammingHelper:
    """Shared helper methods for linear programming optimization."""

    @staticmethod
    def planning_years(current_year, simulation_options):
        """Get planning years for the optimization horizon.

        Args:
            current_year: The current year
            simulation_options: Simulation options dictionary

        Returns:
            List of planning years
        """
        end_year = current_year + simulation_options['rolling_planning_horizon_in_years']
        planning_year_increment = 1
        planning_years = create_time_span(current_year, end_year, planning_year_increment)
        return planning_years
