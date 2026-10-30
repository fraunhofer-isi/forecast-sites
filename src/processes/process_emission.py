# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from processes.process_emission_calculator import ProcessEmissionCalculator


class ProcessEmission:
    """
    Calculates emissions of a process (delegates pure calculations to calculator).

    This class maintains the original method structure for backward compatibility
    with existing tests while extracting pure calculation logic to
    ProcessEmissionCalculator for reusability.
    """

    def __init__(self, process):
        self._process = process

    @property
    def captured_emission_in_t_co2_per_process_count(self):
        """Captured emission per process execution."""
        capture_rate = self._process.carbon_capture_rate
        captured_emissions = self.captured_input_emission_in_t_co2_per_process_count * capture_rate
        return captured_emissions

    @property
    def captured_input_emission_in_t_co2_per_process_count(self):
        """Whether process can capture emissions (1 if capture process, 0 otherwise)."""
        if self._process.is_capture_process:
            return 1
        return 0

    def _direct_emissions_of_energy_demands_in_t_co2_per_process_count(self, year):
        """Sum direct emissions from energy demands (delegates to calculator)."""
        return ProcessEmissionCalculator.sum_energy_demand_emissions(self._process.demands, year)

    def direct_emissions_in_t_co2_per_process_count(self, year):
        """Direct emissions per process execution (scope 1: energy + non-energy)."""
        non_energy_direct = self._process.non_energy_direct_process_emission_in_t_co2_per_process_count
        energy_direct = self._direct_emissions_of_energy_demands_in_t_co2_per_process_count(year)
        return non_energy_direct + energy_direct

    def direct_emissions_in_t_co2(self, year, process_execution_count):
        """Total direct emissions (scope 1)."""
        direct_per_count = self.direct_emissions_in_t_co2_per_process_count(year)
        return ProcessEmissionCalculator.multiply_per_count(direct_per_count, process_execution_count)

    def captured_emission_in_t_co2(self, process_execution_count):
        """Total captured emissions."""
        per_count = self.captured_emission_in_t_co2_per_process_count
        return ProcessEmissionCalculator.multiply_per_count(per_count, process_execution_count)

    def direct_emission_cost_in_euro(
        self,
        year,
        process_execution_count,
        co2_price_in_euro_per_t_co2,
    ):
        """Cost of direct emissions."""
        direct_emissions = self.direct_emissions_in_t_co2(year, process_execution_count)
        return direct_emissions * co2_price_in_euro_per_t_co2

    def direct_emission_cost_in_euro_per_process_count(
        self,
        year,
        co2_price_in_euro_per_t_co2,
    ):
        """Direct emission cost per process execution."""
        non_energy_cost = self.direct_non_energy_emission_cost_in_euro_per_process_count(co2_price_in_euro_per_t_co2)
        energy_cost = self.direct_energy_emission_cost_in_euro_per_process_count(year, co2_price_in_euro_per_t_co2)
        return non_energy_cost + energy_cost

    def savings_due_to_captured_emissions_in_euro_per_process_count(self, co2_price_in_euro_per_t_co2):
        """Calculate savings from captured emissions per process execution."""
        per_count = self.captured_emission_in_t_co2_per_process_count
        return per_count * co2_price_in_euro_per_t_co2

    def direct_energy_emissions_in_t_co2(self, year, process_execution_count):
        """Direct energy-related emissions (scope 1 from energy only)."""
        per_count = self._direct_emissions_of_energy_demands_in_t_co2_per_process_count(year)
        return ProcessEmissionCalculator.multiply_per_count(per_count, process_execution_count)

    def direct_energy_emission_cost_in_euro(self, year, process_execution_count, co2_price_in_euro_per_t_co2):
        """Cost of direct energy-related emissions."""
        direct_energy = self.direct_energy_emissions_in_t_co2(year, process_execution_count)
        return direct_energy * co2_price_in_euro_per_t_co2

    def direct_energy_emission_cost_in_euro_per_process_count(
        self,
        year,
        co2_price_in_euro_per_t_co2,
    ):
        """Energy-related emission cost per process execution (delegates to calculator)."""
        return ProcessEmissionCalculator.sum_energy_demand_costs(self._process.demands, year, co2_price_in_euro_per_t_co2)

    def direct_non_energy_emissions_in_t_co2(self, process_execution_count):
        """Direct non-energy emissions."""
        per_count = self._process.non_energy_direct_process_emission_in_t_co2_per_process_count
        return ProcessEmissionCalculator.multiply_per_count(per_count, process_execution_count)

    def direct_non_energy_emission_cost_in_euro(self, process_execution_count, co2_price_in_euro_per_t_co2):
        """Cost of direct non-energy emissions."""
        direct_non_energy = self.direct_non_energy_emissions_in_t_co2(process_execution_count)
        return direct_non_energy * co2_price_in_euro_per_t_co2

    def direct_non_energy_emission_cost_in_euro_per_process_count(self, co2_price_in_euro_per_t_co2):
        """Non-energy emission cost per process execution."""
        per_count = self._process.non_energy_direct_process_emission_in_t_co2_per_process_count
        return per_count * co2_price_in_euro_per_t_co2

    def saving_due_to_captured_emission_in_euro(self, process_execution_count, co2_price_in_euro_per_t_co2):
        """Total savings from captured emissions."""
        captured = self.captured_emission_in_t_co2(process_execution_count)
        return captured * co2_price_in_euro_per_t_co2

    def energy_carrier_production_direct_emissions_in_t_co2(self, process_execution_count):
        """Direct emissions attributed to each output carrier (delegates to calculator)."""
        return ProcessEmissionCalculator.emissions_by_carrier(
            self._process.output_carriers, self._process, process_execution_count
        )

    def emissions_in_t_co2(self, _process_execution_count):
        """
        Clarify scope of emission calculations as placeholder.

        Currently, scope 3 emissions are calculated only at the production unit
        level, not for individual processes (upstream emissions are aggregated).
        """
        message = (
            'Until now, we calculate scope 3 emissions only on level of production unit. '
            'If you want to consider them on lower levels, you need to calculate them as nested sum.'
        )
        raise NotImplementedError(message)
