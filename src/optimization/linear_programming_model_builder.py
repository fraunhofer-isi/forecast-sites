# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Linear Programming model builder for constraint and objective coefficient construction."""

import numpy as np

from carrier.carrier_unit import CarrierUnit
from optimization.linear_programming_constraint import LinearProgrammingConstraint
from optimization.linear_programming_helper import LinearProgrammingHelper
from processes.installed_process import InstalledProcess
from utils.time_utils import create_time_span


class LinearProgrammingModelBuilder:
    """Builds the linear programming model including objective coefficients and constraints."""

    def __init__(self, optimization):
        """
        Initialize the model builder.

        Args:
            optimization: The LinearProgrammingOptimization instance providing context.

        """
        self._optimization = optimization

    def objective_coefficients(self, year, interest_rate, simulation_options):
        """
        Calculate objective coefficients for all variables (processes and carriers).

        Args:
            year: The current year.
            interest_rate: The interest rate for discounting.
            simulation_options: Simulation options dictionary.

        Returns:
            List of objective coefficients for processes followed by carriers.

        """
        # Call through optimization to allow test patches
        process_option_coefficients = self._optimization._objective_coefficients_for_process_options(
            year,
            interest_rate,
            simulation_options,
        )
        # Call through optimization to allow test patches
        carrier_coefficients = self._optimization._objective_coefficients_for_carriers(
            year,
            interest_rate,
            simulation_options,
        )
        coefficients = process_option_coefficients + carrier_coefficients

        if len(coefficients) != self._optimization.number_of_variables:
            message = (
                f'Length of objective coefficient vector ({len(coefficients)}) does not '
                f'match number of variables ({self._optimization.number_of_variables}).'
            )
            raise ValueError(message)

        return coefficients

    def inequality_constraints(self, year, simulation_options):
        """
        Build inequality constraints for the linear programming problem.

        Args:
            year: The current year.
            simulation_options: Simulation options dictionary.

        Returns:
            Tuple of (constraint_matrix, constraint_vector).

        """
        constraints = []

        # Call through optimization to allow test patches
        production_constraints = self._optimization._production_constraints(year, simulation_options)
        constraints += production_constraints

        # Call through optimization to allow test patches
        carrier_constraints = self._optimization._carrier_purchase_constraints(year, simulation_options)
        constraints += carrier_constraints

        # Call through optimization to allow test patches
        capture_mechanism_constraints = self._optimization._capture_mechanism_constraints(year)
        constraints += capture_mechanism_constraints

        # Call through optimization to allow test patches
        emission_constraints = self._optimization._emission_constraints(year, simulation_options)
        constraints += emission_constraints

        # Call through optimization to allow test patches
        a_ub, b_ub = self._optimization._constraints_to_linprog_format(constraints)
        return a_ub, b_ub

    def determine_bounds(self):
        """
        Determine variable bounds for the linear programming problem.

        All variables are non-negative with no upper bound.

        Returns:
            List of (lower_bound, upper_bound) tuples.

        """
        # We assume that all variables are non-negative and have no upper bound
        variable_range = range(self._optimization.number_of_variables)
        bounds = [(0, None) for _ in variable_range]
        return bounds

    # ========== Private Helper Methods ==========

    @staticmethod
    def _planning_years(current_year, simulation_options):
        """Get planning years for the optimization horizon."""
        return LinearProgrammingHelper.planning_years(current_year, simulation_options)

    @staticmethod
    def _constraints_to_linprog_format(constraints):
        """Convert constraint objects to scipy linprog format."""
        coefficient_matrix = np.array([constraint.matrix_coefficients for constraint in constraints])
        coefficient_vector = np.array([constraint.reference_value for constraint in constraints])
        return coefficient_matrix, coefficient_vector

    def _objective_coefficients_for_process_options(self, current_year, interest_rate, simulation_options):
        """Calculate objective coefficients for all process options."""
        # Call through optimization to allow test patches
        invest_process_cost = self._optimization._invest_process_cost_in_euro_per_process_count(
            current_year, interest_rate, simulation_options
        )

        total_process_cost = invest_process_cost  # initial value for starting the loop over the years

        planning_years = self._planning_years(current_year, simulation_options)

        for year in planning_years:
            co2_price_in_euro_per_t_co2 = self._optimization._context.co2_cost_in_euro_per_t_co2(year)
            # Call through optimization to allow test patches
            annual_process_costs = self._optimization._annual_process_cost_in_euro_per_process_count(
                year,
                self._optimization._process_options,
                co2_price_in_euro_per_t_co2,
                simulation_options,
            )
            # Call through optimization to allow test patches
            discounted_annual_process_costs = self._optimization._discounted_annual_process_costs_in_euro_per_process_count(
                year,
                current_year,
                annual_process_costs,
                interest_rate,
            )
            total_process_cost += np.array(discounted_annual_process_costs)
        total_process_cost = list(total_process_cost)

        return total_process_cost

    def _invest_process_cost_in_euro_per_process_count(
        self,
        current_year,
        interest_rate,
        simulation_options,
    ):
        """Calculate investment costs for processes."""
        is_start_year = current_year == simulation_options['start_year']
        capex_factor = simulation_options.get('start_year_capex_factor', 1.0) if is_start_year else 1.0

        process_cost = []
        for process_option in self._optimization._process_options:
            process = process_option.process

            # New process investments are charged in full when built, not pro-rated
            # across years. This prevents unrealistic switching in rolling horizons.
            # (InstalledProcess.invest_cost already returns ~0 repair cost and ignores the factor.)
            # The investment funding is deducted by Process.invest_cost_in_euro_per_process_count,
            # which scales the CAPEX by the factor before deducting the funding, so that fully
            # funded processes are still penalized in the start year.
            invest_process_cost = process.invest_cost_in_euro_per_process_count(
                current_year,
                interest_rate,
                simulation_options,
                capex_factor,
            )
            process_cost.append(invest_process_cost)
        return process_cost

    def _objective_coefficients_for_carriers(
        self,
        year,
        interest_rate,
        simulation_options,
    ):
        """Calculate objective coefficients for all carriers."""
        carrier_costs_in_euro_per_unit = []
        for carrier in self._optimization._carriers:
            # Call through optimization instance to allow test patches to work
            carrier_cost = self._optimization._carrier_cost_in_euro_per_unit(carrier, year, interest_rate, simulation_options)
            carrier_costs_in_euro_per_unit.append(carrier_cost)
        return carrier_costs_in_euro_per_unit

    def _carrier_cost_in_euro_per_unit_impl(
        self,
        carrier,
        current_year,
        interest_rate,
        simulation_options,
    ):
        """Calculate carrier cost (internal, not patchable by tests)."""
        carrier_cost = 0

        planning_years = self._planning_years(current_year, simulation_options)
        for year in planning_years:
            # Call through optimization to allow test patches to work
            carrier_cost_for_year = self._optimization._carrier_cost_in_euro_per_unit_for_year(carrier, year, simulation_options)
            discounted_carrier_cost_for_year = carrier_cost_for_year / (1 + interest_rate) ** (year - current_year)
            carrier_cost += discounted_carrier_cost_for_year
        return carrier_cost

    @staticmethod
    def _annual_process_cost_in_euro_per_process_count(
        year,
        process_options,
        co2_price_in_euro_per_t_co2,
        simulation_options,
    ):
        """Calculate annual operating costs for all processes."""
        costs = []
        for process_option in process_options:
            process = process_option.process
            cost = process.annual_cost_in_euro_per_process_count(year, co2_price_in_euro_per_t_co2, simulation_options)
            costs.append(cost)
        return np.array(costs)

    @staticmethod
    def _discounted_annual_process_costs_in_euro_per_process_count(
        year,
        current_year,
        annual_process_costs_in_euro_per_process_count,
        interest_rate,
    ):
        """Apply discounting to annual process costs."""
        discounted_annual_process_costs = annual_process_costs_in_euro_per_process_count / (1 + interest_rate) ** (
            year - current_year
        )
        return discounted_annual_process_costs

    def _carrier_cost_in_euro_per_unit_for_year(self, carrier, year, simulation_options):
        """Calculate carrier cost including purchase price, taxes, and emissions."""
        purchase_price_in_euro_per_unit = carrier.purchase_price_in_euro_per_unit(year)
        sell_price_in_euro_per_unit = carrier.sell_price_in_euro_per_unit(year)
        taxes_in_euro_per_unit = carrier.taxes_in_euro_per_unit(year, simulation_options)
        subsidies_in_euro_per_unit = carrier.subsidies_in_euro_per_unit(year, simulation_options)
        co2_price_in_euro_per_t_co2 = self._optimization._context.co2_cost_in_euro_per_t_co2(year)
        upstream_emission_in_t_co2_per_unit = carrier.upstream_emission_in_t_co2_per_unit(year, simulation_options)
        renewably_bound_co2_emission_in_t_co2_per_unit = carrier.renewably_bound_co2_emission_in_t_co2_per_unit(
            year, simulation_options
        )
        downstream_emission_in_t_co2_per_unit = carrier.downstream_emission_in_t_co2_per_unit(year, simulation_options)

        upstream_emission_cost = upstream_emission_in_t_co2_per_unit * co2_price_in_euro_per_t_co2
        bound_emission_cost = -renewably_bound_co2_emission_in_t_co2_per_unit * co2_price_in_euro_per_t_co2
        downstream_emission_cost = downstream_emission_in_t_co2_per_unit * co2_price_in_euro_per_t_co2

        return (
            purchase_price_in_euro_per_unit
            + taxes_in_euro_per_unit
            - subsidies_in_euro_per_unit
            - sell_price_in_euro_per_unit
            + upstream_emission_cost
            + downstream_emission_cost
            + bound_emission_cost
        )

    def _constraint(self, reference_value, label=None):
        """Create a constraint object."""
        constraint = LinearProgrammingConstraint(
            self._optimization.number_of_process_options,
            self._optimization.number_of_carriers,
            reference_value,
            label,
        )
        return constraint

    def _production_constraints(self, year, simulation_options):
        """Build production capacity constraints."""
        constraints = []

        for process_option_index, process_option in enumerate(self._optimization._process_options):
            process = process_option.process
            if isinstance(process, InstalledProcess):
                process_capacity = process.available_process_execution_count(year)
            elif process.tech_available_at_year > year:
                process_capacity = 0
            else:
                process_capacity = 10e40

            # Call through optimization to allow test patches
            process_constraint = self._optimization._constraint(process_capacity, 'production')

            # set the processes coefficients
            process_constraint.process_option_coefficients[process_option_index] = 1

            constraints.append(process_constraint)

        for carrier_index, carrier in enumerate(self._optimization._carriers):
            # Call through optimization to allow test patches
            required_constraint = self._optimization._minimum_export_constraint(year, simulation_options, carrier_index, carrier)
            constraints.append(required_constraint)

            # Call through optimization to allow test patches
            maximum_constraint = self._optimization._maximum_production_constraint(year, carrier_index, carrier)
            constraints.append(maximum_constraint)

        return constraints

    def _carrier_purchase_constraints(self, year, simulation_options):
        """Build carrier purchase and usage constraints."""
        constraints = []

        # Call through optimization to allow test patches
        availability_constraints = self._optimization._carrier_availability_constraints(year)
        constraints += availability_constraints

        # Call through optimization to allow test patches
        minimum_use_constraints = self._optimization._carrier_minimum_use_constraints(year, simulation_options)
        constraints += minimum_use_constraints

        return constraints

    def _capture_mechanism_constraints(self, year):
        """Build constraints for capture mechanisms."""
        # set the right side of the constraint
        # Call through optimization to allow test patches
        constraint = self._optimization._constraint(0, 'capture_mechanism')

        # set processes coefficients
        for process_option_index, process_option in enumerate(self._optimization._process_options):
            process = process_option.process

            direct_emissions = max(process.emission.direct_emissions_in_t_co2_per_process_count(year), 0)  # exludes DAC
            captured_input_emissions = process.emission.captured_input_emission_in_t_co2_per_process_count
            emission_coefficient = direct_emissions - captured_input_emissions

            constraint.process_option_coefficients[process_option_index] = -emission_coefficient

        # set carrier coefficients
        for carrier_index, _carrier in enumerate(self._optimization._carriers):
            constraint.carrier_coefficients[carrier_index] = 0

        constraints = [constraint]
        return constraints

    def _emission_constraints(self, year, simulation_options):
        """Build emission limit constraints."""
        # set the right side of the constraint
        emission_limit_in_t_co2 = simulation_options['emission_limit_in_t_co2']
        # Call through optimization to allow test patches
        constraint = self._optimization._constraint(emission_limit_in_t_co2, 'emission')

        # set processes coefficients
        for process_option_index, process_option in enumerate(self._optimization._process_options):
            process = process_option.process
            # Call through optimization to allow test patches
            constraint.process_option_coefficients[process_option_index] = (
                self._optimization._process_emission_constraint_coefficient(
                    process,
                    year,
                    simulation_options,
                )
            )

        # set carrier coefficients
        for carrier_index, carrier in enumerate(self._optimization._carriers):
            # Call through optimization to allow test patches
            constraint.carrier_coefficients[carrier_index] = self._optimization._carrier_emission_constraint_coefficient(
                carrier,
                year,
                simulation_options,
            )

        constraints = [constraint]
        return constraints

    def _process_emission_constraint_coefficient(self, process, year, simulation_options):
        """Calculate emission coefficient for a process in the emission constraint."""
        # Keep emission component composition in sync with MultiPeriodOptimization
        # and ProductionUnit.budget_relevant_emission_in_t_co2.
        scope = simulation_options['emission_constraint_scope']
        coefficient = 0.0

        if 'direct' in scope:
            direct_emissions = process.emission.direct_emissions_in_t_co2_per_process_count(year)
            captured_emissions = process.emission.captured_emission_in_t_co2_per_process_count
            coefficient += direct_emissions - captured_emissions

        if 'downstream' not in scope:
            return coefficient

        downstream_emission = sum(
            process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
            * self._carrier_downstream_emission_per_unit(carrier, year, simulation_options)
            for carrier in self._optimization._carriers
        )
        return coefficient + downstream_emission

    def _carrier_emission_constraint_coefficient(self, carrier, year, simulation_options):
        """Calculate emission coefficient for a carrier in the emission constraint."""
        # Keep emission component composition in sync with MultiPeriodOptimization
        # and ProductionUnit.budget_relevant_emission_in_t_co2.
        scope = simulation_options['emission_constraint_scope']
        coefficient = 0.0

        if 'upstream' in scope:
            coefficient += carrier.upstream_emission_in_t_co2_per_unit(year, simulation_options)

        if 'renewably_bound' in scope:
            coefficient -= carrier.renewably_bound_co2_emission_in_t_co2_per_unit(year, simulation_options)

        if 'downstream' not in scope:
            return coefficient

        return coefficient + self._carrier_downstream_emission_per_unit(carrier, year, simulation_options)

    @staticmethod
    def _carrier_downstream_emission_per_unit(carrier, year, simulation_options):
        """Get carrier's downstream emission per unit."""
        if not hasattr(carrier, 'downstream_emission_in_t_co2_per_unit'):
            return 0.0
        return carrier.downstream_emission_in_t_co2_per_unit(year, simulation_options)

    def _minimum_export_constraint(self, year, simulation_options, carrier_index, carrier):
        """Build minimum export constraint for a carrier."""
        # set the right side of constraint
        # Call through optimization to allow test patches
        minimum_export = self._optimization._minimum_export(
            carrier,
            year,
            simulation_options,
        )
        # Call through optimization to allow test patches
        required_constraint = self._optimization._constraint(-minimum_export, 'minimum_export')

        # set the processes coefficients
        for process_option_index, process_option in enumerate(self._optimization._process_options):
            process = process_option.process
            export_per_process_count = process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
            required_constraint.process_option_coefficients[process_option_index] = -export_per_process_count

        # set a -1 in the diagonal of the carrier coefficients
        required_constraint.carrier_coefficients[carrier_index] = -1

        return required_constraint

    def _maximum_production_constraint(self, year, carrier_index, carrier):
        """Build maximum production constraint for a carrier."""
        # set right side of constraint
        maximum_production_amount = carrier.maximum_production_in_unit
        # Call through optimization to allow test patches
        maximum_constraint = self._optimization._constraint(maximum_production_amount, 'maximum_production')

        # set the processes coefficients
        for process_option_index, process_option in enumerate(self._optimization._process_options):
            process = process_option.process
            export_per_process_count = process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
            maximum_constraint.process_option_coefficients[process_option_index] = export_per_process_count

        # set a 1 in the diagonal of the carrier coefficients
        maximum_constraint.carrier_coefficients[carrier_index] = 1

        return maximum_constraint

    def _minimum_export(
        self,
        carrier,
        year,
        simulation_options,
    ):
        """Get minimum export amount for a carrier."""
        unit = carrier.unit
        if unit is CarrierUnit.T:
            minimum_export = self._optimization._production_unit.carrier_minimum_export_in_t(
                carrier,
                year,
                simulation_options,
            )
        elif unit is CarrierUnit.GJ:
            minimum_export = 0
        else:
            message = f'Unknown carrier unit: {unit}'
            raise TypeError(message)
        return minimum_export

    def _carrier_availability_constraints(self, year):
        """Build carrier availability constraints."""
        constraints = []
        for carrier_index, carrier in enumerate(self._optimization._carriers):
            # set right side of the constraint
            availability = self._optimization._production_unit.carrier_availability(carrier, year)
            # Call through optimization to allow test patches
            constraint = self._optimization._constraint(availability, 'availability')

            # set a 1 in the diagonal of the carrier coefficients
            constraint.carrier_coefficients[carrier_index] = 1
            constraints.append(constraint)
        return constraints

    def _carrier_minimum_use_constraints(self, year, simulation_options):
        """Build carrier minimum use constraints."""
        constraints = []
        for carrier_index, carrier in enumerate(self._optimization._carriers):
            # set right side of the constraint
            minimum_use = carrier.minimum_use_in_unit(year, simulation_options)
            # Call through optimization to allow test patches
            constraint = self._optimization._constraint(-minimum_use, 'minimum_use')

            # sets -1 in the diagonal of the carrier coefficients
            constraint.carrier_coefficients[carrier_index] = -1
            constraints.append(constraint)
        return constraints
