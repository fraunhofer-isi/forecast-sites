# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class Optimization:
    def __init__(
        self,
        year,
        production_unit,
        context,
    ):
        self._year = year
        self._production_unit = production_unit
        self._context = context

    def optimize(self):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    @property
    def _process_options(self):
        processes = self._production_unit.available_process_options
        return processes

    @property
    def _carriers(self):
        carriers = self._production_unit.available_carriers
        return carriers

    @property
    def number_of_process_options(self):
        length = len(self._process_options)
        return length

    @property
    def number_of_carriers(self):
        length = len(self._carriers)
        return length
