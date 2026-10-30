# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from interpolation.interpolator import interpolate


class Demand:
    def __init__(
        self,
        carrier,
        efficiency_improvement_interpolation_data,
        simulation_options,
    ):
        self.carrier = carrier
        self._efficiency_improvement_interpolation_data = efficiency_improvement_interpolation_data
        self._simulation_options = simulation_options

    def purchase_cost_in_euro_per_process_count(self, year):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def opportunity_cost_in_euro_per_process_count(self, year, co2_price_in_euro_per_t_co2):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def subsidies_in_euro_per_process_count(self, year, simulation_options):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def taxes_in_euro_per_process_count(self, year, simulation_options):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def _efficiency_factor(self, year):
        efficiency_improvement = self._efficiency_improvement(year)
        efficiency_factor = 1 - efficiency_improvement
        return efficiency_factor

    def _efficiency_improvement(self, year):
        efficiency_improvement = interpolate(
            year,
            self._simulation_options,
            self._efficiency_improvement_interpolation_data,
        )
        return efficiency_improvement
