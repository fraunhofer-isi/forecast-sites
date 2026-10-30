# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


from scipy import optimize as scipy_optimize

from optimization.linear_programming_model_builder import LinearProgrammingModelBuilder
from optimization.linear_programming_result_parser import LinearProgrammingResultParser
from optimization.optimization import Optimization


class LinearProgrammingOptimization(Optimization):
    def __init__(self, year, production_unit, context):
        """
        Initialize linear programming optimization.

        The linear programming problem is formulated as:
            minimize c x, with
            a_ub x <= b_ub
            a_eq x = b_eq
            lower_bounds <= x <= upper_bounds

        where:
            x is the variable vector (consisting of processes variables and energy carrier variables)
            c is the objective coefficient row vector
            a_ub is the inequality constraint matrix
            b_ub is the inequality constraint vector
            a_eq is the equality constraint matrix
            b_eq is the equality constraint vector
            lower_bounds is the lower bound vector
            upper_bounds is the upper bound vector

        See:
            https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html
            https://en.wikipedia.org/wiki/Linear_programming
        """
        super().__init__(year, production_unit, context)

        simulation_options = self._context.simulation_options
        interest_rate = self._context.interest_rate

        # Build model using dedicated builder
        self._builder = LinearProgrammingModelBuilder(self)
        self._c = self._builder.objective_coefficients(year, interest_rate, simulation_options)
        self._a_ub, self._b_ub = self._builder.inequality_constraints(year, simulation_options)

        # currently we do not use equality constraints:
        self._a_eq = None
        self._b_eq = None

        self._bounds = self._builder.determine_bounds()

    def optimize(self):
        """Solve the linear programming problem and return optimization result."""
        linear_programming_result = scipy_optimize.linprog(
            self._c,
            A_ub=self._a_ub,
            b_ub=self._b_ub,
            A_eq=self._a_eq,
            b_eq=self._b_eq,
            bounds=self._bounds,
            method='highs',
            options={
                'presolve': True,  # simplifies problem
                'time_limit': 10,  # seconds
                'primal_feasibility_tolerance': 1e-6,  # tolerance for feasibility checks
                'dual_feasibility_tolerance': 1e-6,  # tolerance for feasibility checks
            },
        )

        parser = LinearProgrammingResultParser(self)
        optimization_result = parser.parse_result(linear_programming_result, self._context.simulation_options)
        return optimization_result

    @property
    def number_of_variables(self):
        number_of_variables = self.number_of_process_options + self.number_of_carriers
        return number_of_variables

    # ========== Backward Compatibility Delegation Methods ==========
    # These methods delegate to LinearProgrammingModelBuilder for backward compatibility with tests

    def _objective_coefficients(self, year, interest_rate, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder().objective_coefficients(year, interest_rate, simulation_options)

    def _inequality_constraints(self, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder().inequality_constraints(year, simulation_options)

    def _determine_bounds(self):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder().determine_bounds()

    @staticmethod
    def _rolling_planning_horizon_end_year(current_year, simulation_options):
        """Kept for backward compatibility."""
        rolling_planning_horizon = simulation_options['rolling_planning_horizon_in_years']
        end_year = current_year + rolling_planning_horizon
        return end_year

    @staticmethod
    def _planning_years(current_year, simulation_options):
        """Kept for backward compatibility."""
        return LinearProgrammingModelBuilder._planning_years(current_year, simulation_options)

    @staticmethod
    def _modeled_year_count(current_year, simulation_options):
        """Kept for backward compatibility."""
        return LinearProgrammingResultParser._modeled_year_count(current_year, simulation_options)

    def _objective_coefficients_for_process_options(self, current_year, interest_rate, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._objective_coefficients_for_process_options(current_year, interest_rate, simulation_options)

    def _invest_process_cost_in_euro_per_process_count(
        self,
        current_year,
        interest_rate,
        simulation_options,
    ):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._invest_process_cost_in_euro_per_process_count(current_year, interest_rate, simulation_options)

    def _objective_coefficients_for_carriers(
        self,
        year,
        interest_rate,
        simulation_options,
    ):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._objective_coefficients_for_carriers(year, interest_rate, simulation_options)

    def _carrier_cost_in_euro_per_unit(
        self,
        carrier,
        current_year,
        interest_rate,
        simulation_options,
    ):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._carrier_cost_in_euro_per_unit_impl(carrier, current_year, interest_rate, simulation_options)

    def _carrier_cost_in_euro_per_unit_for_year(self, carrier, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._carrier_cost_in_euro_per_unit_for_year(carrier, year, simulation_options)

    @staticmethod
    def _annual_process_cost_in_euro_per_process_count(
        year,
        process_options,
        co2_price_in_euro_per_t_co2,
        simulation_options,
    ):
        """Kept for backward compatibility."""
        return LinearProgrammingModelBuilder._annual_process_cost_in_euro_per_process_count(
            year, process_options, co2_price_in_euro_per_t_co2, simulation_options
        )

    @staticmethod
    def _discounted_annual_process_costs_in_euro_per_process_count(
        year,
        current_year,
        annual_process_costs_in_euro_per_process_count,
        interest_rate,
    ):
        """Kept for backward compatibility."""
        return LinearProgrammingModelBuilder._discounted_annual_process_costs_in_euro_per_process_count(
            year, current_year, annual_process_costs_in_euro_per_process_count, interest_rate
        )

    def _constraint(self, reference_value, label=None):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._constraint(reference_value, label)

    def _production_constraints(self, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._production_constraints(year, simulation_options)

    def _carrier_purchase_constraints(self, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._carrier_purchase_constraints(year, simulation_options)

    def _capture_mechanism_constraints(self, year):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._capture_mechanism_constraints(year)

    def _emission_constraints(self, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._emission_constraints(year, simulation_options)

    def _process_emission_constraint_coefficient(self, process, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._process_emission_constraint_coefficient(process, year, simulation_options)

    def _carrier_emission_constraint_coefficient(self, carrier, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._carrier_emission_constraint_coefficient(carrier, year, simulation_options)

    @staticmethod
    def _carrier_downstream_emission_per_unit(carrier, year, simulation_options):
        """Kept for backward compatibility."""
        return LinearProgrammingModelBuilder._carrier_downstream_emission_per_unit(carrier, year, simulation_options)

    def _minimum_export_constraint(self, year, simulation_options, carrier_index, carrier):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._minimum_export_constraint(year, simulation_options, carrier_index, carrier)

    def _maximum_production_constraint(self, year, carrier_index, carrier):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._maximum_production_constraint(year, carrier_index, carrier)

    def _get_builder(self):
        """Get or create builder instance. Handles cases where instance wasn't properly initialized."""
        if not hasattr(self, '_builder') or self._builder is None:
            self._builder = LinearProgrammingModelBuilder(self)
        return self._builder

    def _minimum_export(self, carrier, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._minimum_export(carrier, year, simulation_options)

    def _carrier_availability_constraints(self, year):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._carrier_availability_constraints(year)

    def _carrier_minimum_use_constraints(self, year, simulation_options):
        """Delegate to builder. Kept for backward compatibility."""
        return self._get_builder()._carrier_minimum_use_constraints(year, simulation_options)

    @staticmethod
    def _constraints_to_linprog_format(constraints):
        """Kept for backward compatibility."""
        return LinearProgrammingModelBuilder._constraints_to_linprog_format(constraints)
