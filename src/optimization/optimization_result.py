# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

logger = logging.getLogger(__name__)

VERY_SMALL_NEGATIVE_PROCESS_EXECUTION_THRESHOLD = 1e-3


class OptimizationResult:
    def __init__(
        self,
        process_execution_counts,
        purchased_carrier_amounts,
        total_cost_in_euro=None,
        modeled_year_count=None,
        selected_rolling_planning_horizon_in_years=None,
        interest_rate=None,
        carrier_netto_amounts=None,
    ):
        self.process_execution_counts = process_execution_counts  # 1
        self.purchased_carrier_amounts = purchased_carrier_amounts  # gj or t
        self.total_cost_in_euro = self._normalized_total_cost(total_cost_in_euro)
        self.modeled_year_count = modeled_year_count
        self.selected_rolling_planning_horizon_in_years = selected_rolling_planning_horizon_in_years
        self.interest_rate = self._normalized_interest_rate(interest_rate)
        self.cost_per_year_in_euro = self._cost_per_year_in_euro()
        # LP-consistent carrier netto amounts: carrier -> float (positive=produced, negative=consumed).
        # When present, ProductionUnit and RegionResultApplier use these instead of
        # recomputing netto from sub-production-unit execution counts, ensuring the
        # reported export equals purchased_LP + netto_LP (the LP's own balance).
        self.carrier_netto_amounts = carrier_netto_amounts if carrier_netto_amounts is not None else {}
        self._validate_and_fix()

    def _normalized_total_cost(self, total_cost_in_euro):
        if total_cost_in_euro is None:
            return None
        return float(total_cost_in_euro)

    def _normalized_interest_rate(self, interest_rate):
        if interest_rate is None:
            return None
        return float(interest_rate)

    def _cost_per_year_in_euro(self):
        if self.total_cost_in_euro is None or self.modeled_year_count is None or self.interest_rate is None:
            return None

        if self.modeled_year_count <= 0:
            message = f'Modeled year count must be positive, got {self.modeled_year_count}.'
            raise ValueError(message)

        if self.interest_rate == 0:
            return self.total_cost_in_euro / self.modeled_year_count

        present_value_factor = (1 + self.interest_rate) ** self.modeled_year_count
        annuity_factor = (self.interest_rate * present_value_factor) / (present_value_factor - 1)
        return self.total_cost_in_euro * annuity_factor

    @property
    def processes(self):
        processes = list(self.process_execution_counts.keys())
        return processes

    @property
    def carriers(self):
        carriers = list(self.purchased_carrier_amounts.keys())
        return carriers

    def _validate_and_fix(self):
        linear_optimization_tolerance = -1e-5
        for (
            process_option,
            process_execution_count,
        ) in self.process_execution_counts.items():
            # Three-tier validation for process execution counts:
            # 1. Hard error for significantly negative values (optimizer bug)
            # 2. Warning for small negative values (numerical noise)
            # 3. Pass-through for non-negative or very small negative values
            if process_execution_count < linear_optimization_tolerance:
                message = f'Process execution count must not be negative for {process_option}: {process_execution_count}'
                raise ValueError(message)
            if process_execution_count < VERY_SMALL_NEGATIVE_PROCESS_EXECUTION_THRESHOLD:
                logger.debug(
                    'Process execution count is slightly negative (%.2e) for %s; treating as 0',
                    process_execution_count,
                    process_option,
                )
                self.process_execution_counts[process_option] = 0

        for carrier, amount in self.purchased_carrier_amounts.items():
            if amount < linear_optimization_tolerance:
                message = f'Purchased carrier amount must not be negative for carrier {carrier}.'
                raise ValueError(message)
