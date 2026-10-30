# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Pure calculation logic for process emissions (extraction from ProcessEmission).

This module contains only pure calculations (no state dependency, no side effects).
Caller provides all required parameters. All methods are @staticmethod.
"""

from carrier.carrier_unit import CarrierUnit
from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand


class ProcessEmissionCalculator:
    """Stateless calculator for process emission metrics."""

    @staticmethod
    def sum_energy_demand_emissions(demands, year):
        """Sum direct emissions from all energy demands."""
        total = 0
        for demand in demands:
            if isinstance(demand, EnergyCarrierEnergyDemand):
                total += demand.direct_emission_in_t_co2_per_process_count(year)
        return total

    @staticmethod
    def multiply_per_count(value_per_count, process_execution_count):
        """Scale per-unit value to total across all executions."""
        return value_per_count * process_execution_count

    @staticmethod
    def sum_energy_demand_costs(demands, year, co2_price):
        """Sum emission costs from all energy demands."""
        total = 0
        for demand in demands:
            if isinstance(demand, EnergyCarrierEnergyDemand):
                total += demand.direct_emission_cost_in_euro_per_process_count(year, co2_price)
        return total

    @staticmethod
    def emissions_by_carrier(output_carriers, process, process_execution_count):
        """Calculate direct emissions attributed to each output carrier (GJ only)."""
        emissions = {}
        for carrier in output_carriers:
            if carrier.unit == CarrierUnit.GJ:
                production_gj = process.production_in_gj(carrier, process_execution_count)
                emission_per_gj = carrier.direct_emission_in_t_co2_per_gj
                emissions[carrier] = production_gj * emission_per_gj
        return emissions
