# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from result.visitor.entity import Entity


class Output(Entity):
    def __init__(self, carrier):
        self.carrier = carrier

    def __repr__(self):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def accept(self, visitor, year):
        enter_results = visitor.enter_output(self, year)
        result = visitor.exit_output(self, year, enter_results)
        return result

    def output_in_euro_per_process_count(self, year, co2_price_in_euro_per_t_co2, simulation_options):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)
