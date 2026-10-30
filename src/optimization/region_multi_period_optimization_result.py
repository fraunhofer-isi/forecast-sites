# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from optimization.carrier_netto_amount_calculator import CarrierNettoAmountCalculator
from optimization.optimization_result import OptimizationResult


class RegionMultiPeriodOptimizationResult:
    """Slices a joint PU x period LP solution into per-PU, per-year results."""

    def __init__(
        self,
        linear_programming_result,
        production_units,
        process_options_by_pu,
        carriers,
        simulation_periods,
        offsets_by_pu,
        new_capacity_offsets_by_pu,
        num_proc_by_pu,
        vars_per_period_by_pu,
        total_cost_in_euro=None,
    ):
        self._production_units = list(production_units)
        self._process_options_by_pu = dict(process_options_by_pu)
        self._carriers = list(carriers)
        self._simulation_periods = list(simulation_periods)
        self.total_cost_in_euro = None if total_cost_in_euro is None else float(total_cost_in_euro)

        solution = linear_programming_result.x

        self._results_by_year = {}
        self._new_capacity_by_year = {}

        for period_index, year in enumerate(simulation_periods):
            year_results = {}
            year_new_capacity = {}

            for pu in production_units:
                proc_options = process_options_by_pu[pu]
                n_proc = num_proc_by_pu[pu]
                vpp = vars_per_period_by_pu[pu]
                pu_offset = offsets_by_pu[pu]
                nc_offset = new_capacity_offsets_by_pu[pu]

                exec_start = pu_offset + period_index * vpp
                process_execution_counts = {po: float(solution[exec_start + i]) for i, po in enumerate(proc_options)}

                carrier_start = exec_start + n_proc
                purchased_carrier_amounts = {c: float(solution[carrier_start + i]) for i, c in enumerate(carriers)}

                carrier_netto_amounts = CarrierNettoAmountCalculator().calculate(process_execution_counts, carriers, year)

                year_results[pu] = OptimizationResult(
                    process_execution_counts,
                    purchased_carrier_amounts,
                    total_cost_in_euro=None,
                    carrier_netto_amounts=carrier_netto_amounts,
                )

                nc_start = nc_offset + period_index * n_proc
                year_new_capacity[pu] = {po: float(solution[nc_start + i]) for i, po in enumerate(proc_options)}

            self._results_by_year[year] = year_results
            self._new_capacity_by_year[year] = year_new_capacity

            logging.debug(
                'Region multi-period result for year %s: %d PUs sliced',
                year,
                len(production_units),
            )

    def has_result_for_year(self, year):
        return year in self._results_by_year

    def result_for_year(self, year):
        return self._results_by_year[year]

    def result_for(self, production_unit, year=None):
        """Return OptimizationResult for a PU. If year is None, use first period."""
        if year is None:
            year = self._simulation_periods[0]
        return self._results_by_year[year][production_unit]

    def new_capacity_for_year(self, year):
        return self._new_capacity_by_year[year]

    @property
    def simulation_periods(self):
        return list(self._simulation_periods)
