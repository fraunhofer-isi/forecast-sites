# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later


class Simulation:
    def __init__(self, simulation_mode, time_span, regions, visitors):
        self.simulation_mode = simulation_mode
        self.regions = regions
        self._time_span = time_span
        self._visitors = visitors
        self._pipeline_cost_scaling = None

    def run(self):
        for year in self._time_span:
            for region in self.regions.values():
                region.process_year(year, self.simulation_mode, self._pipeline_cost_scaling)
                for visitor in self._visitors:
                    region.accept(visitor, year)

        for visitor in self._visitors:
            visitor.finalize()
