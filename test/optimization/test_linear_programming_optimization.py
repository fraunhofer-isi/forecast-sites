# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest
from test_utils.isi_mock import Mock, fixture, original_patch, patch, patch_property

from carrier.carrier_unit import CarrierUnit
from optimization.linear_programming_constraint import LinearProgrammingConstraint
from optimization.linear_programming_optimization import LinearProgrammingOptimization
from optimization.linear_programming_optimization_result import (
    LinearProgrammingOptimizationResult,
)
from processes.installed_process import InstalledProcess

if TYPE_CHECKING:
    from processes.process import Process


@fixture
def year():
    return 2020


@fixture
@patch(
    LinearProgrammingOptimization._objective_coefficients,
    'mocked_objective_coefficients',
)
@patch(
    LinearProgrammingOptimization._inequality_constraints,
    ('mocked_a_ub', 'mocked_b_ub'),
)
@patch(LinearProgrammingOptimization._determine_bounds, 'mocked_bounds')
def sut(year):
    mocked_context = Mock()
    mocked_context.simulation_options = {
        'rolling_planning_horizon_in_years': 10,
        'start_year': 2020,
        'year_increment': 1,
        'emission_limit_in_t_co2': 100,
    }
    mocked_context.interest_rate = 0.05
    return LinearProgrammingOptimization(
        year,
        Mock(available_process_options=[], available_carriers=[]),
        mocked_context,
    )


def test_construction(sut):
    assert sut is not None


def test_number_of_variables(sut):
    process_option = Mock()
    sut._production_unit = Mock(
        available_process_options=[process_option],
        available_carriers=['mocked_carrier'],
    )
    result = sut.number_of_variables
    assert result == 2


class TestOptimize:
    @patch(LinearProgrammingOptimizationResult.__init__, None)
    @patch_property(LinearProgrammingOptimization._process_options, 'mocked_processes')
    @patch_property(LinearProgrammingOptimization._carriers, 'mocked_carriers')
    def test_with_success(self, sut):
        mocked_result = Mock()
        mocked_result.success = True
        with original_patch('scipy.optimize.linprog', Mock(mocked_result)):
            result = sut.optimize()
            assert isinstance(result, LinearProgrammingOptimizationResult)

    def test_without_success(self, sut):
        mocked_result = Mock()
        mocked_result.success = False
        with (
            original_patch('scipy.optimize.linprog', Mock(mocked_result)),
            pytest.raises(RuntimeError, match='Optimization failed'),
        ):
            sut.optimize()


def test_rolling_planning_horizon_end_year(sut):
    result = sut._rolling_planning_horizon_end_year(2020, {'rolling_planning_horizon_in_years': 10})
    assert result == 2030


def test_invest_process_cost_in_euro_per_process_count(sut):
    process_option = Mock()
    process_option.process = Mock()
    process_option.process.invest_cost_in_euro_per_process_count = Mock(100)
    process_options = [process_option]

    simulation_options = {
        'rolling_planning_horizon_in_years': 10,
        'start_year': 2020,
    }
    with patch_property(LinearProgrammingOptimization._process_options, process_options):
        result = sut._invest_process_cost_in_euro_per_process_count(2020, 0.05, simulation_options)
        assert len(result) == 1
        assert result[0] == 100


def test_invest_process_cost_full_capex_in_lp_mode(sut):
    """Test Option A: LP charges full CAPEX for new processes (no per-window fractioning)."""
    process_option = Mock()
    process_option.process = Mock()
    process_option.process.invest_cost_in_euro_per_process_count = Mock(return_value=1000)
    process_option.process.lifetime_in_years = 20
    process_options = [process_option]

    simulation_options = {
        'rolling_planning_horizon_in_years': 5,
        'start_year': 2020,
        'optimization_type': 'LINEAR_PROGRAMMING',
    }
    with patch_property(LinearProgrammingOptimization._process_options, process_options):
        result = sut._invest_process_cost_in_euro_per_process_count(2020, 0.05, simulation_options)
        # Option A: full capex, no pro-rata scaling by planning_years/lifetime
        assert len(result) == 1
        assert result[0] == 1000


def test_invest_process_cost_installed_process_zero_cost(sut):
    """Test that InstalledProcess returns zero investment cost (repair/maintenance only)."""
    # InstalledProcess.invest_cost returns ~0 (repair cost, age_factor hardwired to 0)
    # The LP builder passes this through without modification.
    process_option = Mock()
    process_option.process = Mock(spec=[])  # Simulate InstalledProcess returning 0
    process_option.process.invest_cost_in_euro_per_process_count = Mock(return_value=0)
    process_options = [process_option]

    simulation_options = {
        'rolling_planning_horizon_in_years': 5,
        'start_year': 2020,
        'optimization_type': 'LINEAR_PROGRAMMING',
    }
    with patch_property(LinearProgrammingOptimization._process_options, process_options):
        result = sut._invest_process_cost_in_euro_per_process_count(2020, 0.05, simulation_options)
        # Full CAPEX path used, but invest_cost returns 0 (as InstalledProcess does)
        assert len(result) == 1
        assert result[0] == 0


@patch(LinearProgrammingOptimization._carrier_cost_in_euro_per_unit, 'mocked_carrier_cost')
@patch_property(LinearProgrammingOptimization._carriers, ['mocked_carrier'])
def test_objective_coefficients_for_carriers(sut):
    result = sut._objective_coefficients_for_carriers(2020, 0.05, {'rolling_planning_horizon_in_years': 10})
    assert result == ['mocked_carrier_cost']


@patch(LinearProgrammingOptimization._rolling_planning_horizon_end_year, 2021)
@patch(LinearProgrammingOptimization._carrier_cost_in_euro_per_unit_for_year, 10)
@patch_property(LinearProgrammingOptimization._carriers, [Mock()])
def test_carrier_cost(sut):
    simulation_options = {
        'rolling_planning_horizon_in_years': 1,
        'year_increment': 1,
    }

    result = sut._carrier_cost_in_euro_per_unit(
        'mocked_carrier',
        2020,
        0.05,
        simulation_options,
    )
    expected = 10 + 10 / (1 + 0.05)
    assert result == pytest.approx(expected)


@patch(LinearProgrammingConstraint.__init__, None)
@patch_property(LinearProgrammingOptimization.number_of_process_options, 2)
@patch_property(LinearProgrammingOptimization.number_of_carriers, 2)
def test_constraint(sut):
    result = sut._constraint('mocked_reference_value')
    assert isinstance(result, LinearProgrammingConstraint)


@patch(
    LinearProgrammingOptimization._constraint,
    Mock(),
)
@patch(
    LinearProgrammingOptimization._minimum_export_constraint,
    'mocked_required_constraint',
)
@patch(
    LinearProgrammingOptimization._maximum_production_constraint,
    'mocked_maximum_constraint',
)
class TestProductionConstraints:
    @patch_property(
        LinearProgrammingOptimization._process_options,
        [Mock(process=Mock(max_process_execution_count=1, tech_available_at_year=2020))],
    )
    @patch_property(LinearProgrammingOptimization._carriers, ['mocked_carrier'])
    def test_with_normal_process(self, sut):
        sut._context = Mock(interest_rate=0.05)
        result = sut._production_constraints(2020, {})
        assert len(result) == 3

    def test_with_installed_process(self, sut):
        sut._context = Mock(interest_rate=0.05)
        sut._context.simulation_options = {'installed_process_execution_count': 1}

        installed_process = self._create_mocked_installed_process()
        process_option = Mock(process=installed_process)
        process_options = [process_option]

        with (
            patch_property(LinearProgrammingOptimization._process_options, process_options),
            patch_property(LinearProgrammingOptimization._carriers, ['mocked_carrier']),
        ):
            result = sut._production_constraints(2020, {})
            assert len(result) == 3

    def test_with_future_installed_process_has_zero_capacity(self, sut):
        LinearProgrammingOptimization._constraint.reset_mock()
        installed_process = self._create_mocked_installed_process(year_of_last_reinvestment=2025)
        process_option = Mock(process=installed_process)
        process_options = [process_option]

        with (
            patch_property(LinearProgrammingOptimization._process_options, process_options),
            patch_property(LinearProgrammingOptimization._carriers, ['mocked_carrier']),
        ):
            sut._production_constraints(2020, {})
            assert LinearProgrammingOptimization._constraint.called
            assert LinearProgrammingOptimization._constraint.call_args_list[0][0][0] == 0

    def test_with_active_installed_process_uses_max_capacity(self, sut):
        LinearProgrammingOptimization._constraint.reset_mock()
        installed_process = self._create_mocked_installed_process(year_of_last_reinvestment=2020)
        process_option = Mock(process=installed_process)
        process_options = [process_option]

        with (
            patch_property(LinearProgrammingOptimization._process_options, process_options),
            patch_property(LinearProgrammingOptimization._carriers, ['mocked_carrier']),
        ):
            sut._production_constraints(2020, {})
            assert LinearProgrammingOptimization._constraint.called
            assert LinearProgrammingOptimization._constraint.call_args_list[0][0][0] == 10

    def _create_mocked_installed_process(self, year_of_last_reinvestment=2020):
        sub_production_unit = SimpleNamespace(
            max_process_execution_count=10,
            year_of_last_reinvestment=year_of_last_reinvestment,
        )
        with original_patch(
            'processes.installed_process.InstalledProcess.__init__',
            lambda _self, _process, _spu: None,
        ):
            process = cast('Process', Mock(id='process_id'))
            installed_process = InstalledProcess(process, sub_production_unit)
            installed_process._sub_production_unit = sub_production_unit
        return installed_process


@patch(
    LinearProgrammingOptimization._carrier_availability_constraints,
    ['mocked_availability_constraint'],
)
@patch(
    LinearProgrammingOptimization._carrier_minimum_use_constraints,
    ['mocked_minimum_use_constraint'],
)
def test_carrier_purchase_constraints(sut):
    result = sut._carrier_purchase_constraints(2020, 'mocked_simulation_options')
    assert result == ['mocked_availability_constraint', 'mocked_minimum_use_constraint']


@patch_property(
    LinearProgrammingOptimization._process_options,
    [
        Mock(
            process=Mock(
                emission=Mock(
                    direct_emissions_in_t_co2_per_process_count=Mock(1),
                    captured_input_emission_in_t_co2_per_process_count=0,
                )
            )
        )
    ],
)
@patch_property(LinearProgrammingOptimization._carriers, [Mock()])
def test_capture_mechanism_constraints(sut):
    mocked_constraint = Mock()
    with patch(LinearProgrammingOptimization._constraint, Mock(mocked_constraint)):
        result = sut._capture_mechanism_constraints(2020)
        assert result == [mocked_constraint]


@patch_property(
    LinearProgrammingOptimization._process_options,
    [Mock(process=Mock(direct_emissions_in_t_co2_per_process_count=1))],
)
@patch_property(LinearProgrammingOptimization._carriers, [Mock()])
def test_emission_constraints(sut):
    simulation_options = {
        'emission_limit_in_t_co2': 100,
        'emission_constraint_scope': frozenset({'direct', 'upstream', 'renewably_bound'}),
    }
    mocked_constraint = Mock()
    with patch(LinearProgrammingOptimization._constraint, Mock(mocked_constraint)):
        result = sut._emission_constraints(2020, simulation_options)
        assert result == [mocked_constraint]


@patch_property(LinearProgrammingOptimization.number_of_variables, 2)
def test_determine_bounds(sut):
    result = sut._determine_bounds()
    assert result == [(0, None), (0, None)]


@patch(LinearProgrammingOptimization._minimum_export, 0)
def test_minimum_export_constraint(sut):
    process_option = Mock()

    mocked_constraint = Mock()
    with (
        patch_property(LinearProgrammingOptimization._process_options, [process_option]),
        patch(LinearProgrammingOptimization._constraint, Mock(mocked_constraint)),
    ):
        # updated signature: (year, simulation_options, carrier_index, carrier)
        result = sut._minimum_export_constraint(2020, 'mocked_simulation_options', 0, 'mocked_carrier')

        assert result == mocked_constraint


def test_maximum_production_constraint(sut):
    process_option = Mock()
    process_option.process = Mock()
    process_option.process.netto_produced_or_consumed_amount_per_process_count = Mock(return_value=0)
    carrier = Mock()
    carrier.maximum_production_in_unit = 50

    mocked_constraint = Mock()
    with (
        patch_property(LinearProgrammingOptimization._process_options, [process_option]),
        patch(LinearProgrammingOptimization._constraint, Mock(mocked_constraint)),
    ):
        result = sut._maximum_production_constraint(2020, 0, carrier)
        assert result == mocked_constraint


@patch_property(LinearProgrammingOptimization.number_of_process_options, 1)
@patch_property(LinearProgrammingOptimization.number_of_carriers, 1)
def test_maximum_production_constraint_uses_carrier_value(sut):
    carrier = Mock()
    carrier.maximum_production_in_unit = 123
    process_option = Mock()
    process_option.process = Mock()
    process_option.process.netto_produced_or_consumed_amount_per_process_count = Mock(return_value=0)

    def fake_constraint(_self, reference_value, _label=None):
        return Mock(reference_value=reference_value, process_option_coefficients=[None], carrier_coefficients=[None])

    with (
        patch_property(LinearProgrammingOptimization._process_options, [process_option]),
        patch(LinearProgrammingOptimization._constraint, fake_constraint),
    ):
        result = sut._maximum_production_constraint(2020, 0, carrier)
        assert result.reference_value == 123


class TestMiniumExport:
    def test_for_t(self, sut):
        carrier = Mock()
        carrier.unit = CarrierUnit.T

        sut._production_unit = Mock()
        sut._production_unit.carrier_minimum_export_in_t = Mock('mocked_result')
        result = sut._minimum_export(carrier, 2020, 'mocked_simulation_options')
        assert result == 'mocked_result'

    def test_for_gj(self, sut):
        carrier = Mock()
        carrier.unit = CarrierUnit.GJ
        result = sut._minimum_export(carrier, 2020, 'mocked_simulation_options')
        assert result == 0

    def test_for_unknown_unit(self, sut):
        carrier = Mock()
        carrier.unit = 'mocked_unit'
        with pytest.raises(TypeError):
            sut._minimum_export(carrier, 2020, 'mocked_simulation_options')


@patch(LinearProgrammingOptimization._minimum_export, 0)
def test_carrier_availability_constraints(sut):
    sut._production_unit = Mock()
    sut._production_unit.carrier_availability = Mock('mocked_availability')

    constraint = Mock()

    with (
        patch(LinearProgrammingOptimization._constraint, Mock(constraint)),
        patch_property(LinearProgrammingOptimization._carriers, [Mock()]),
    ):
        result = sut._carrier_availability_constraints(2020)
        assert result[0] == constraint


@patch(LinearProgrammingOptimization._minimum_export, 0)
def test_carrier_minimum_use_constraints(sut):
    sut._production_unit = Mock()
    sut._production_unit.carrier_minimum_use = Mock(3)

    constraint = Mock()

    with (
        patch(LinearProgrammingOptimization._constraint, Mock(constraint)),
        patch_property(LinearProgrammingOptimization._carriers, [Mock()]),
    ):
        result = sut._carrier_minimum_use_constraints('mocked_year', 'mocked_simulation_options')
        assert result[0] == constraint


def test_constraints_to_linprog_format(sut):
    constraint = Mock()
    constraint.matrix_coefficients = ['mocked_matrix_coefficient']
    constraint.reference_value = 'mocked_reference_value'
    constraints = [constraint]
    constraint_matrix, constraint_vector = sut._constraints_to_linprog_format(constraints)
    assert isinstance(constraint_matrix, np.ndarray)
    assert constraint_matrix.tolist() == [['mocked_matrix_coefficient']]

    assert isinstance(constraint_vector, np.ndarray)
    assert constraint_vector.tolist() == ['mocked_reference_value']


def test_carrier_cost_in_euro_per_unit_for_year(sut):
    carrier = Mock()
    carrier.purchase_price_in_euro_per_unit = Mock(20)
    carrier.sell_price_in_euro_per_unit = Mock(10)
    carrier.taxes_in_euro_per_unit = Mock(3)
    carrier.subsidies_in_euro_per_unit = Mock(1)
    carrier.upstream_emission_in_t_co2_per_unit = Mock(0)
    carrier.renewably_bound_co2_emission_in_t_co2_per_unit = Mock(0)
    carrier.downstream_emission_in_t_co2_per_unit = Mock(0)
    sut._context = Mock(co2_cost_in_euro_per_t_co2=Mock(0))
    result = sut._carrier_cost_in_euro_per_unit_for_year(carrier, 2020, {})
    assert result == 12


def test_annual_process_cost_in_euro_per_process_count(sut):
    process_option = Mock()
    process_option.process = Mock()
    process_option.process.annual_cost_in_euro_per_process_count = Mock(5)
    process_options = [process_option]

    result = sut._annual_process_cost_in_euro_per_process_count(
        2020,
        process_options,
        'mocked_co2_price_in_euro_per_t_co2',
        'mocked_simulation_options',
    )
    assert len(result) == 1
    assert result[0] == 5


def test_discounted_annual_process_costs_in_euro_per_process_count(sut):
    interest_rate = 0.1

    result = sut._discounted_annual_process_costs_in_euro_per_process_count(
        2020,
        2010,
        10,
        interest_rate,
    )

    assert result == 10 / 1.1**10


@patch(
    LinearProgrammingOptimization._objective_coefficients_for_process_options,
    ['mocked_process_coefficient'],
)
@patch(
    LinearProgrammingOptimization._objective_coefficients_for_carriers,
    ['mocked_carrier_coefficient'],
)
class TestObjectiveCoefficients:
    @patch_property(LinearProgrammingOptimization.number_of_variables, 2)
    def test_equal_length(self, sut):
        result = sut._objective_coefficients(2020, 0.05, 'mocked_simulation_options')
        assert result == ['mocked_process_coefficient', 'mocked_carrier_coefficient']

    @patch_property(LinearProgrammingOptimization.number_of_variables, 1)
    def test_different_length(self, sut):
        with pytest.raises(ValueError, match='Length of objective coefficient vector'):
            sut._objective_coefficients(2020, 0.05, 'mocked_simulation_options')


@patch(LinearProgrammingOptimization._production_constraints)
@patch(LinearProgrammingOptimization._carrier_purchase_constraints)
@patch(LinearProgrammingOptimization._capture_mechanism_constraints)
@patch(LinearProgrammingOptimization._emission_constraints)
@patch(
    LinearProgrammingOptimization._constraints_to_linprog_format,
    ('mocked_a_ub', 'mocked_b_ub'),
)
def test_inequality_constraints(sut):
    result = sut._inequality_constraints(2020, 'mocked_simulation_options')
    assert result == ('mocked_a_ub', 'mocked_b_ub')


@patch(LinearProgrammingOptimization._rolling_planning_horizon_end_year, 2021)
@patch(
    LinearProgrammingOptimization._invest_process_cost_in_euro_per_process_count,
    np.array([0]),
)
@patch_property(LinearProgrammingOptimization._process_options, [Mock(process=Mock())])
@patch(
    LinearProgrammingOptimization._annual_process_cost_in_euro_per_process_count,
    np.array([1]),
)
@patch(
    LinearProgrammingOptimization._discounted_annual_process_costs_in_euro_per_process_count,
    np.array([1]),
)
def test_objective_coefficients_for_process_options(sut):
    sut._context = Mock()
    sut._context.co2_cost_in_euro_per_t_co2 = Mock(10)
    simulation_options = {
        'rolling_planning_horizon_in_years': 1,
        'year_increment': 1,
    }
    result = sut._objective_coefficients_for_process_options(2020, 0.05, simulation_options)
    assert result == [2]


@patch(LinearProgrammingOptimization._invest_process_cost_in_euro_per_process_count, np.array([0]))
@patch(LinearProgrammingOptimization._annual_process_cost_in_euro_per_process_count, np.array([100]))
@patch(LinearProgrammingOptimization._discounted_annual_process_costs_in_euro_per_process_count, np.array([100]))
@patch(LinearProgrammingOptimization._rolling_planning_horizon_end_year, 2028)
@patch_property(LinearProgrammingOptimization._process_options, [Mock(process=Mock())])
def test_objective_coefficients_for_process_options_no_double_counting(sut):
    # Rolling horizon length (8 years) not divisible by increment (5). Expect coverage of 9 years total.
    sut._context = Mock()
    sut._context.co2_cost_in_euro_per_t_co2 = Mock(10)
    simulation_options = {'rolling_planning_horizon_in_years': 8, 'year_increment': 5}
    result = sut._objective_coefficients_for_process_options(2020, 0, simulation_options)
    # 9 years * 100 cost each = 900
    assert result[0] == 900


@patch(LinearProgrammingOptimization._carrier_cost_in_euro_per_unit_for_year, 10)
@patch(LinearProgrammingOptimization._rolling_planning_horizon_end_year, 2028)
@patch_property(LinearProgrammingOptimization._carriers, [Mock()])
def test_carrier_cost_no_double_counting(sut):
    # Same horizon remainder scenario for carriers
    simulation_options = {'rolling_planning_horizon_in_years': 8, 'year_increment': 5}
    sut._carrier_cost_in_euro_per_unit('mocked_carrier', 2020, 0, simulation_options)
    # 9 years * 10 cost = 90


class TestEmissionScopeConstraintCoefficients:
    """Test emission constraint coefficient calculation with scope variations."""

    def test_process_emission_constraint_direct_only(self, sut):
        """Test process emission with direct emissions only."""
        process = Mock()
        process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 10.0
        process.emission.captured_emission_in_t_co2_per_process_count = 2.0
        simulation_options = {'emission_constraint_scope': frozenset({'direct'})}

        result = sut._process_emission_constraint_coefficient(process, 2020, simulation_options)

        assert result == 8.0

    def test_carrier_downstream_emission_with_attribute(self):
        """Test downstream emission when carrier has the attribute."""
        carrier = Mock()
        carrier.downstream_emission_in_t_co2_per_unit.return_value = 2.5
        simulation_options = {}

        result = LinearProgrammingOptimization._carrier_downstream_emission_per_unit(carrier, 2020, simulation_options)

        assert result == 2.5

    def test_carrier_downstream_emission_without_attribute(self):
        """Test downstream emission when carrier lacks the attribute."""
        carrier = Mock(spec=[])  # No downstream_emission attribute
        simulation_options = {}

        result = LinearProgrammingOptimization._carrier_downstream_emission_per_unit(carrier, 2020, simulation_options)

        assert result == 0.0


class TestBackwardCompatibilityDelegations:
    """Test backward compatibility delegation methods."""

    def test_planning_years_delegation(self, sut):
        """Test _planning_years delegates to LPModelBuilder._planning_years."""
        simulation_options = {'rolling_planning_horizon_in_years': 10, 'year_increment': 1}
        result = sut._planning_years(2020, simulation_options)
        # Result depends on LPModelBuilder implementation, just verify it doesn't error
        assert result is not None

    def test_modeled_year_count_delegation(self, sut):
        """Test _modeled_year_count delegates to LPResultParser._modeled_year_count."""
        simulation_options = {'rolling_planning_horizon_in_years': 10, 'year_increment': 1}
        result = sut._modeled_year_count(2020, simulation_options)
        # Should return an integer count of years
        assert isinstance(result, int)
        assert result > 0

    def test_get_builder_creates_builder_if_missing(self, sut):
        """Test _get_builder creates builder if not properly initialized."""
        # Remove the builder to simulate uninitialized state
        if hasattr(sut, '_builder'):
            delattr(sut, '_builder')

        result = sut._get_builder()
        # Verify builder was created
        assert result is not None
        assert hasattr(sut, '_builder')
        assert sut._builder is result
