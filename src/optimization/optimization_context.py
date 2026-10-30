# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class OptimizationContext:
    def __init__(
        self,
        co2_cost_in_euro_per_t_co2,
        interest_rate,
        simulation_options,
    ):
        self.co2_cost_in_euro_per_t_co2 = co2_cost_in_euro_per_t_co2
        self.interest_rate = interest_rate
        self.simulation_options = simulation_options
