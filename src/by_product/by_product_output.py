# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from output.output import Output


class ByProductOutput(Output):
    def __init__(self, by_product, output_in_t_per_process_count):
        super().__init__(by_product)
        self.output_in_t_per_process_count = output_in_t_per_process_count

    def __repr__(self):
        class_name = type(self).__name__
        return f'{class_name}({self.carrier}: {self.output_in_t_per_process_count})'

    @property
    def by_product(self):
        return self.carrier

    def output_in_euro_per_process_count(self, year, co2_price_in_euro_per_t_co2, simulation_options):
        output = self.output_in_t_per_process_count
        price = self.by_product.sell_price_in_euro_per_t(year)
        downstream_emission = self.by_product.downstream_emission_in_t_co2_per_unit(year, simulation_options)
        emission_adjusted_price = price - downstream_emission * co2_price_in_euro_per_t_co2
        gain_in_euro_per_process_count = output * emission_adjusted_price
        return gain_in_euro_per_process_count

    def output_in_t(self, execution_count):
        production = execution_count * self.output_in_t_per_process_count
        return production
