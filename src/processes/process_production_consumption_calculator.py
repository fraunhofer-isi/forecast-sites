# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Production and consumption calculations for processes.

This module encapsulates unit conversion and carrier flow calculations,
separating material balance logic from core process logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from carrier.carrier_unit import CarrierUnit

if TYPE_CHECKING:
    from demand.demand import Demand
    from output.output import Output


class ProcessProductionConsumptionCalculator:
    """
    Calculator for process production and consumption flows.

    Handles unit conversions and netto carrier flows,
    supporting both tonne (T) and gigajoule (GJ) units.
    """

    def __init__(self, outputs: tuple[Output], demands: tuple[Demand]):
        """
        Initialize with process outputs and demands.

        Args:
            outputs: Tuple of output definitions (carriers produced).
            demands: Tuple of demand definitions (carriers consumed).

        """
        self._outputs = outputs
        self._demands = demands

    def netto_produced_or_consumed_amount_per_process_count(self, year: int, carrier: Any) -> float:
        """
        Get netto (net) carrier amount: production minus consumption.

        Positive value = net production (excess available)
        Negative value = net consumption (deficit must import or purchase)

        Args:
            year: Year for which to calculate consumption.
            carrier: Carrier to calculate flow for.

        Returns:
            Net amount per process execution (production - consumption).

        """
        production = self._production_in_unit_per_process_count(carrier)
        consumption = self._consumption_in_unit_per_process_count(year, carrier)
        return production - consumption

    def production_in_gj(self, carrier: Any, process_execution_count: float) -> float:
        """
        Calculate total production in gigajoules.

        Args:
            carrier: Carrier to calculate production for.
            process_execution_count: Number of times process executes.

        Returns:
            Total production in GJ = production_per_count * execution_count.

        """
        production_per_count = self._production_in_gj_per_process_count(carrier)
        return production_per_count * process_execution_count

    def _production_in_unit_per_process_count(self, carrier: Any) -> float:
        """
        Get production in native carrier units per process execution.

        Converts to carrier's native unit (T or GJ) and sums across outputs.

        Args:
            carrier: Carrier to calculate production for.

        Returns:
            Production per process execution in carrier's native unit.

        Raises:
            TypeError: If carrier unit is not T or GJ.

        """
        carrier_unit = carrier.unit
        if carrier_unit is CarrierUnit.T:
            return self._production_in_t_per_process_count(carrier)
        if carrier_unit is CarrierUnit.GJ:
            return self._production_in_gj_per_process_count(carrier)
        msg = f'Unknown carrier unit: {carrier_unit}'
        raise TypeError(msg)

    def _production_in_t_per_process_count(self, carrier: Any) -> float:
        """
        Get production in tonnes per process execution.

        Sums output from all outputs that produce this carrier.

        Args:
            carrier: Carrier to calculate production for.

        Returns:
            Production in tonnes per process execution.

        """
        production = 0.0
        for output in self._outputs:
            if output.carrier == carrier:
                production += output.output_in_t_per_process_count
        return production

    def _production_in_gj_per_process_count(self, carrier: Any) -> float:
        """
        Get production in gigajoules per process execution.

        Sums energy output from all outputs that produce this carrier.

        Args:
            carrier: Carrier to calculate production for.

        Returns:
            Production in GJ per process execution.

        """
        production = 0.0
        for output in self._outputs:
            if output.carrier == carrier:
                production += output.output_in_gj_per_process_count
        return production

    def _consumption_in_unit_per_process_count(self, year: int, carrier: Any) -> float:
        """
        Get consumption in native carrier units per process execution.

        Converts to carrier's native unit (T or GJ) and sums across demands.

        Args:
            year: Year for which to calculate consumption.
            carrier: Carrier to calculate consumption for.

        Returns:
            Consumption per process execution in carrier's native unit.

        Raises:
            TypeError: If carrier unit is not T or GJ.

        """
        carrier_unit = carrier.unit
        if carrier_unit is CarrierUnit.T:
            return self._consumption_in_t_per_process_count(year, carrier)
        if carrier_unit is CarrierUnit.GJ:
            return self._consumption_in_gj_per_process_count(year, carrier)
        msg = f'Unknown carrier unit: {carrier_unit}'
        raise TypeError(msg)

    def _consumption_in_t_per_process_count(self, year: int, carrier: Any) -> float:
        """
        Get consumption in tonnes per process execution.

        Sums demand from all demands for this carrier in given year.

        Args:
            year: Year for which to calculate consumption.
            carrier: Carrier to calculate consumption for.

        Returns:
            Consumption in tonnes per process execution.

        """
        consumption = 0.0
        for demand in self._demands:
            if demand.carrier == carrier:
                consumption += demand.demand_in_t_per_process_count(year)
        return consumption

    def _consumption_in_gj_per_process_count(self, year: int, energy_carrier: Any) -> float:
        """
        Get consumption in gigajoules per process execution.

        Sums energy demand from all demands for this carrier in given year.

        Args:
            year: Year for which to calculate consumption.
            energy_carrier: Energy carrier to calculate consumption for.

        Returns:
            Consumption in GJ per process execution.

        """
        consumption = 0.0
        for demand in self._demands:
            if demand.carrier == energy_carrier:
                consumption += demand.demand_in_gj_per_process_count(year)
        return consumption
