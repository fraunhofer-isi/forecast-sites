# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from output.output import Output


class EnergyCarrierOutput(Output):
    def __init__(self, energy_carrier, output_in_gj_per_process_count):
        super().__init__(energy_carrier)
        self.output_in_gj_per_process_count = output_in_gj_per_process_count

    def __repr__(self):
        class_name = type(self).__name__
        return f'{class_name}({self.carrier}: {self.output_in_gj_per_process_count})'

    @property
    def energy_carrier(self):
        return self.carrier

    def output_in_euro_per_process_count(self, year, co2_price_in_euro_per_t_co2, simulation_options):
        output = self.output_in_gj_per_process_count
        price = self.energy_carrier.sell_price_in_euro_per_gj(year)
        downstream_emission = self.energy_carrier.downstream_emission_in_t_co2_per_unit(year, simulation_options)
        emission_adjusted_price = price - downstream_emission * co2_price_in_euro_per_t_co2
        cost_in_euro_per_process_count = output * emission_adjusted_price
        return cost_in_euro_per_process_count

    def output_in_gj(self, execution_count):
        production = execution_count * self.output_in_gj_per_process_count
        return production
