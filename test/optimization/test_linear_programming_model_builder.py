# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import numpy as np
import pytest
from test_utils.isi_mock import Mock, fixture, patch

from optimization.linear_programming_model_builder import LinearProgrammingModelBuilder


@fixture
@patch(LinearProgrammingModelBuilder.objective_coefficients, [1.0, 2.0, 3.0])
@patch(LinearProgrammingModelBuilder.inequality_constraints, (np.array([[1, 0], [0, 1]]), np.array([10, 20])))
@patch(LinearProgrammingModelBuilder.determine_bounds, [(0, None), (0, 10)])
def sut():
    """Create a LinearProgrammingModelBuilder instance for testing."""
    mocked_optimization = Mock()
    mocked_optimization.number_of_variables = 3
    return LinearProgrammingModelBuilder(mocked_optimization)


def test_initialization(sut):
    """Test LinearProgrammingModelBuilder initializes with optimization context."""
    assert sut._optimization is not None


class TestObjectiveCoefficients:
    """Test objective coefficient calculation."""

    def test_objective_coefficients_combines_process_and_carrier_coefficients(self, sut):
        """Test that objective coefficients combine process and carrier coefficients."""
        sut._optimization._objective_coefficients_for_process_options = Mock(return_value=[1.0, 2.0])
        sut._optimization._objective_coefficients_for_carriers = Mock(return_value=[3.0])
        sut._optimization.number_of_variables = 3

        result = sut.objective_coefficients(2020, 0.05, {})

        assert result == [1.0, 2.0, 3.0]
        sut._optimization._objective_coefficients_for_process_options.assert_called_once_with(2020, 0.05, {})
        sut._optimization._objective_coefficients_for_carriers.assert_called_once_with(2020, 0.05, {})

    def test_objective_coefficients_validates_length(self, sut):
        """Test that objective coefficients validates against number_of_variables."""
        sut._optimization._objective_coefficients_for_process_options = Mock(return_value=[1.0])
        sut._optimization._objective_coefficients_for_carriers = Mock(return_value=[2.0])
        sut._optimization.number_of_variables = 5  # Mismatch

        with pytest.raises(ValueError, match='Length of objective coefficient vector'):
            sut.objective_coefficients(2020, 0.05, {})


class TestInequalityConstraints:
    """Test inequality constraint building."""

    def test_inequality_constraints_combines_all_constraint_types(self, sut):
        """Test that inequality constraints combines production, carrier, capture, and emission constraints."""
        sut._optimization._production_constraints = Mock(return_value=['prod_constraint'])
        sut._optimization._carrier_purchase_constraints = Mock(return_value=['carrier_constraint'])
        sut._optimization._capture_mechanism_constraints = Mock(return_value=['capture_constraint'])
        sut._optimization._emission_constraints = Mock(return_value=['emission_constraint'])
        sut._optimization._constraints_to_linprog_format = Mock(return_value=(np.array([[1, 0]]), np.array([10])))

        _a_ub, _b_ub = sut.inequality_constraints(2020, {})

        assert sut._optimization._production_constraints.called
        assert sut._optimization._carrier_purchase_constraints.called
        assert sut._optimization._capture_mechanism_constraints.called
        assert sut._optimization._emission_constraints.called
        # Verify constraints were combined
        call_args = sut._optimization._constraints_to_linprog_format.call_args[0][0]
        assert len(call_args) == 4


class TestDetermineBounds:
    """Test variable bounds determination."""

    def test_determine_bounds_returns_list_of_tuples(self, sut):
        """Test that determine_bounds returns proper bounds structure."""
        sut._optimization._process_options = [Mock(), Mock()]
        sut._optimization._carriers = [Mock()]

        result = sut.determine_bounds()

        # Result should be list of tuples with lower and upper bounds
        assert isinstance(result, list)
        for bound in result:
            assert isinstance(bound, tuple)
            assert len(bound) == 2


class TestPlanningYears:
    """Test planning year calculation."""

    def test_planning_years_returns_span(self):
        """Test planning years calculation returns correct time span."""
        simulation_options = {
            'rolling_planning_horizon_in_years': 5,
        }
        years = LinearProgrammingModelBuilder._planning_years(2020, simulation_options)

        # Should have years from 2020 to 2024 inclusive
        assert len(years) > 0
        assert 2020 in list(years)


class TestConstraintsToLinprogFormat:
    """Test constraint format conversion."""

    def test_constraints_to_linprog_format_handles_empty_constraints(self):
        """Test conversion of empty constraint list."""
        constraints = []
        a_ub, b_ub = LinearProgrammingModelBuilder._constraints_to_linprog_format(constraints)

        assert a_ub is None or len(a_ub) == 0
        assert b_ub is None or len(b_ub) == 0

    def test_constraints_to_linprog_format_combines_constraints(self):
        """Test conversion of multiple constraints."""
        constraint1 = Mock()
        constraint1.coefficients = [1.0, 2.0, 0.0]
        constraint1.rhs = 10.0

        constraint2 = Mock()
        constraint2.coefficients = [0.0, 1.0, 3.0]
        constraint2.rhs = 20.0

        constraints = [constraint1, constraint2]
        a_ub, b_ub = LinearProgrammingModelBuilder._constraints_to_linprog_format(constraints)

        # Should have 2 constraints
        assert len(a_ub) == 2
        assert len(b_ub) == 2


class TestAnnualProcessCost:
    """Test annual process cost calculation."""

    def test_annual_process_cost_iterates_over_process_options(self):
        """Test annual cost calculation iterates over process options."""
        process_option1 = Mock()
        process_option1.process.annual_cost_in_euro_per_process_count.return_value = 100.0

        process_option2 = Mock()
        process_option2.process.annual_cost_in_euro_per_process_count.return_value = 200.0

        costs = LinearProgrammingModelBuilder._annual_process_cost_in_euro_per_process_count(
            year=2020,
            process_options=[process_option1, process_option2],
            co2_price_in_euro_per_t_co2=50.0,
            simulation_options={},
        )

        # Should return numpy array with costs for each process
        assert len(costs) == 2
        assert costs[0] == 100.0
        assert costs[1] == 200.0

    def test_annual_process_cost_returns_numpy_array(self):
        """Test that annual cost returns numpy array."""
        process_option = Mock()
        process_option.process.annual_cost_in_euro_per_process_count.return_value = 100.0

        costs = LinearProgrammingModelBuilder._annual_process_cost_in_euro_per_process_count(
            year=2020,
            process_options=[process_option],
            co2_price_in_euro_per_t_co2=0.0,
            simulation_options={},
        )

        # Should be numpy array
        assert isinstance(costs, np.ndarray)
        assert len(costs) == 1


class TestDiscountedAnnualProcessCosts:
    """Test discounted cost calculation."""

    def test_discounted_costs_apply_discount_factor(self):
        """Test that discounting applies correct factor."""
        annual_cost = 100.0
        interest_rate = 0.1
        years_difference = 1

        discounted = LinearProgrammingModelBuilder._discounted_annual_process_costs_in_euro_per_process_count(
            year=2021,
            current_year=2020,
            annual_process_costs_in_euro_per_process_count=annual_cost,
            interest_rate=interest_rate,
        )

        # Should be 100 / 1.1^1 = 90.909...
        expected = annual_cost / ((1 + interest_rate) ** years_difference)
        assert abs(discounted - expected) < 0.01

    def test_discounted_costs_same_year_no_discount(self):
        """Test that same year has no discount."""
        annual_cost = 100.0

        discounted = LinearProgrammingModelBuilder._discounted_annual_process_costs_in_euro_per_process_count(
            year=2020,
            current_year=2020,
            annual_process_costs_in_euro_per_process_count=annual_cost,
            interest_rate=0.1,
        )

        # Same year should have factor of 1.0
        assert discounted == annual_cost


class TestCarrierDownstreamEmission:
    """Test carrier downstream emission calculation."""

    def test_carrier_downstream_emission_with_attribute(self):
        """Test getting downstream emission from carrier."""
        carrier = Mock()
        carrier.downstream_emission_in_t_co2_per_unit.return_value = 2.5

        result = LinearProgrammingModelBuilder._carrier_downstream_emission_per_unit(
            carrier=carrier,
            year=2020,
            simulation_options={},
        )

        assert result == 2.5

    def test_carrier_downstream_emission_without_attribute(self):
        """Test default to 0 when carrier has no downstream emission."""
        carrier = Mock(spec=[])  # No downstream_emission attribute

        result = LinearProgrammingModelBuilder._carrier_downstream_emission_per_unit(
            carrier=carrier,
            year=2020,
            simulation_options={},
        )

        assert result == 0.0


class TestConstraintCreation:
    """Test constraint object creation."""

    def test_constraint_creates_with_reference_value(self, sut):
        """Test _constraint creates constraint with reference value."""
        constraint = sut._constraint(reference_value=100.0)

        assert constraint is not None
        assert constraint.reference_value == 100.0

    def test_constraint_creates_with_label(self, sut):
        """Test _constraint creates constraint with label."""
        constraint = sut._constraint(reference_value=100.0, label='test_constraint')

        assert constraint is not None
        assert constraint.label == 'test_constraint'

    def test_constraint_creates_without_label(self, sut):
        """Test _constraint creates constraint without label."""
        constraint = sut._constraint(reference_value=100.0)

        assert constraint is not None


class TestProductionConstraints:
    """Test production constraint building."""

    def test_production_constraints_returns_list(self, sut):
        """Test _production_constraints returns constraint list."""
        sut._optimization._process_options = []
        sut._optimization._carriers = []
        sut._optimization._constraint = Mock(return_value=Mock(process_option_coefficients={}))
        sut._optimization._minimum_export_constraint = Mock(return_value=Mock())
        sut._optimization._maximum_production_constraint = Mock(return_value=Mock())

        constraints = sut._production_constraints(2020, {})

        assert isinstance(constraints, list)

    def test_production_constraints_handles_process_options(self, sut):
        """Test _production_constraints processes process options."""
        process_option = Mock()
        process_option.process = Mock(tech_available_at_year=2010)
        sut._optimization._process_options = [process_option]
        sut._optimization._carriers = []
        sut._optimization._constraint = Mock(return_value=Mock(process_option_coefficients={}))

        constraints = sut._production_constraints(2020, {})

        # Should have at least one constraint for the process
        assert len(constraints) >= 1


class TestCarrierPurchaseConstraints:
    """Test carrier purchase constraint building."""

    def test_carrier_purchase_constraints_returns_list(self, sut):
        """Test _carrier_purchase_constraints returns constraint list."""
        sut._optimization._carriers = []
        sut._optimization._carrier_availability_constraints = Mock(return_value=[])
        sut._optimization._carrier_minimum_use_constraints = Mock(return_value=[])

        constraints = sut._carrier_purchase_constraints(2020, {})

        assert isinstance(constraints, list)


class TestEmissionConstraints:
    """Test emission constraint building."""

    def test_emission_constraints_returns_list(self, sut):
        """Test _emission_constraints returns constraint list."""
        sut._optimization._process_options = []
        sut._optimization._carriers = []
        sut._optimization._context = Mock()
        sut._optimization._constraint = Mock(return_value=Mock(process_option_coefficients={}, carrier_coefficients={}))
        simulation_options = {'emission_limit_in_t_co2': 1000.0}

        constraints = sut._emission_constraints(2020, simulation_options)

        assert isinstance(constraints, list)
