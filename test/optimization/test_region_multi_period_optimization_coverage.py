# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for RegionMultiPeriodOptimization constraint and objective building."""

import unittest
from unittest import mock

import pytest

from carrier.carrier_unit import CarrierUnit
from optimization.region_multi_period_optimization import RegionMultiPeriodOptimization
from processes.installed_process import InstalledProcess


def _create_mock_carrier(unit=CarrierUnit.GJ, max_production=1000.0):
    carrier = mock.MagicMock()
    carrier.unit = unit
    carrier.maximum_production_in_unit = max_production
    carrier.purchase_price_in_euro_per_unit.return_value = 10.0
    carrier.sell_price_in_euro_per_unit.return_value = 2.0
    carrier.taxes_in_euro_per_unit.return_value = 1.0
    carrier.subsidies_in_euro_per_unit.return_value = 0.5
    carrier.upstream_emission_in_t_co2_per_unit.return_value = 0.1
    carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.02
    carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.05
    carrier.minimum_use_in_unit.return_value = 0.0
    return carrier


def _create_mock_installed_process():
    process = mock.MagicMock(spec=InstalledProcess)
    process.invest_cost_in_euro_per_process_count.return_value = 5.0
    process.annual_cost_in_euro_per_process_count.return_value = 10.0
    process.available_process_execution_count.return_value = 5.0
    process.netto_produced_or_consumed_amount_per_process_count.return_value = 2.0
    process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 3.0
    process.emission.captured_emission_in_t_co2_per_process_count = 0.5
    process.emission.captured_input_emission_in_t_co2_per_process_count = 0.1
    return process


def _create_mock_template_process(tech_available_at_year=2015):
    process = mock.MagicMock()
    process.invest_cost_in_euro_per_process_count.return_value = 200.0
    process.annual_cost_in_euro_per_process_count.return_value = 20.0
    process.capex_in_euro_per_process_count.return_value = 500.0
    process.net_capex_in_euro_per_process_count.return_value = 500.0
    process.tech_available_at_year = tech_available_at_year
    process.lifetime_in_years = 30
    process.netto_produced_or_consumed_amount_per_process_count.return_value = 3.0
    process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 1.0
    process.emission.captured_emission_in_t_co2_per_process_count = 0.2
    process.emission.captured_input_emission_in_t_co2_per_process_count = 0.0
    return process


def _create_mock_production_unit(carriers, process_options):
    pu = mock.MagicMock()
    pu.available_carriers = carriers
    pu.available_process_options = process_options
    pu.carrier_minimum_export_in_t.return_value = 0.0
    pu.carrier_availability.return_value = 100.0
    site = mock.MagicMock()
    site.can_purchase.return_value = True
    site.shared_pool_for.return_value = site
    site.carrier_availability.return_value = 100.0
    site.group = None
    pu._site = site
    return pu


def _build_rmpo(emission_scope=None, budget=None, tech_available=2015):
    """Build a RegionMultiPeriodOptimization with real constraint building."""
    if emission_scope is None:
        emission_scope = ['direct', 'downstream']

    carrier = _create_mock_carrier(unit=CarrierUnit.GJ)
    installed_process = _create_mock_installed_process()
    template_process = _create_mock_template_process(tech_available_at_year=tech_available)

    po1 = mock.MagicMock()
    po1.process = installed_process
    po2 = mock.MagicMock()
    po2.process = template_process

    pu = _create_mock_production_unit([carrier], [po1, po2])

    mock_region = mock.MagicMock()
    mock_context = mock.MagicMock()
    sim_opts = {
        'rolling_planning_horizon_in_years': 5,
        'year_increment': 5,
        'start_year': 2020,
        'end_year': 2025,
        'start_year_capex_factor': 0.8,
        'emission_constraint_scope': emission_scope,
        'emission_limit_in_t_co2': 1000.0,
    }
    if budget is not None:
        sim_opts['overall_emission_budget_in_t_co2'] = budget
    mock_context.simulation_options = sim_opts
    mock_context.interest_rate = 0.05
    mock_context.co2_cost_in_euro_per_t_co2.return_value = 50.0

    return RegionMultiPeriodOptimization(2020, mock_region, [pu], mock_context)


class TestRegionMultiPeriodOptimizationCoverage(unittest.TestCase):
    """Cover missing lines in RegionMultiPeriodOptimization."""

    def test_construction_builds_objective_and_constraints(self):
        """Test constructor builds objective with exec, carrier, and new_capacity coefficients (lines 89, 140-155, 168-182)."""
        rmpo = _build_rmpo()

        assert rmpo._c is not None
        assert len(rmpo._c) == rmpo._total_variables
        assert rmpo._a_ub is not None
        assert rmpo._b_ub is not None
        # new_capacity_index should be used (line 89)
        assert rmpo._total_variables > 0

    def test_new_capacity_cost_uses_capex_net_of_funding(self):
        """Test the capex factor is applied before the funding is deducted and salvage refers to the net capex."""
        rmpo = _build_rmpo()
        pu = rmpo._production_units[0]
        template_process = rmpo._process_options_by_pu[pu][1].process
        template_process.net_capex_in_euro_per_process_count.side_effect = lambda _year, _options, factor=1.0: (
            500.0 * factor - 200.0
        )
        simulation_options = rmpo._context.simulation_options

        objective = rmpo._build_objective(0.05, simulation_options)

        # start year 2020: capex factor 0.8 -> 500 * 0.8 - 200 = 200
        net_capex = 200.0
        salvage = rmpo._salvage_value_in_euro(net_capex, 2020, 30, 0.05, simulation_options)
        assert objective[rmpo._new_capacity_index(pu, 0, 1)] == pytest.approx(net_capex - salvage)
        template_process.net_capex_in_euro_per_process_count.assert_any_call(2020, simulation_options, 0.8)

    def test_fully_funded_process_stays_penalized_in_start_year(self):
        """Regression guard for D1: the start year factor must not be neutralized by full funding."""
        rmpo = _build_rmpo()
        pu = rmpo._production_units[0]
        template_process = rmpo._process_options_by_pu[pu][1].process

        # Fully funded process: funding equals the unscaled capex.
        template_process.net_capex_in_euro_per_process_count.side_effect = lambda _year, _options, factor=1.0: max(
            500.0 * factor - 500.0, 0.0
        )
        simulation_options = dict(rmpo._context.simulation_options)
        simulation_options['start_year_capex_factor'] = 5.0

        objective = rmpo._build_objective(0.05, simulation_options)

        # 500 * 5 - 500 = 2000 > 0; deducting the funding first would collapse this to 0.
        assert objective[rmpo._new_capacity_index(pu, 0, 1)] > 0

    def test_capacity_linking_constraints(self):
        """Test _capacity_linking_constraints for template processes (lines 366-383)."""
        rmpo = _build_rmpo()
        pu = rmpo._production_units[0]

        rows = rmpo._capacity_linking_constraints(pu)

        # Template process should have linking constraints
        assert len(rows) > 0

    def test_capacity_linking_constraints_unavailable_process(self):
        """Test _capacity_linking_constraints when process not yet available (lines 371-375)."""
        # Template process not available until 2030 (after all simulation periods)
        rmpo = _build_rmpo(tech_available=2030)
        pu = rmpo._production_units[0]

        rows = rmpo._capacity_linking_constraints(pu)

        # Should have constraints forcing exec to 0 for unavailable periods
        assert len(rows) > 0

    def test_overall_emission_budget_constraint(self):
        """Test _overall_emission_budget_constraint with budget set (lines 391-407)."""
        rmpo = _build_rmpo(budget=5000.0)

        rows = rmpo._overall_emission_budget_constraint(rmpo._context.simulation_options)

        assert len(rows) == 1
        _, budget_value = rows[0]
        assert budget_value == 5000.0

    def test_overall_emission_budget_constraint_no_budget(self):
        """Test _overall_emission_budget_constraint without budget returns empty."""
        rmpo = _build_rmpo(budget=None)

        rows = rmpo._overall_emission_budget_constraint(rmpo._context.simulation_options)

        assert rows == []

    def test_process_emission_coefficient_without_direct(self):
        """Test _process_emission_coefficient without direct scope (branch 415->420)."""
        rmpo = _build_rmpo(emission_scope=['downstream'])
        process = rmpo._production_units[0].available_process_options[0].process

        result = rmpo._process_emission_coefficient(process, 2020, {'emission_constraint_scope': ['downstream']})

        # No direct, only downstream
        assert result is not None

    def test_process_emission_coefficient_with_downstream(self):
        """Test _process_emission_coefficient with downstream (lines 423-428)."""
        rmpo = _build_rmpo(emission_scope=['direct', 'downstream'])
        process = rmpo._production_units[0].available_process_options[0].process

        result = rmpo._process_emission_coefficient(process, 2020, {'emission_constraint_scope': ['direct', 'downstream']})

        assert result != 0

    def test_carrier_emission_coefficient_downstream(self):
        """Test _carrier_emission_coefficient with downstream (line 440)."""
        rmpo = _build_rmpo()
        carrier = rmpo._carriers[0]

        result = rmpo._carrier_emission_coefficient(carrier, 2020, {'emission_constraint_scope': ['downstream']})

        assert result == pytest.approx(0.05, abs=0.01)

    def test_build_bounds_installed_process(self):
        """Test _build_bounds sets (0,0) for installed process new_capacity (line 475)."""
        rmpo = _build_rmpo()

        bounds = rmpo._build_bounds()

        # Should have bounds for all variables
        assert len(bounds) == rmpo._total_variables
        # Some bounds should be (0, 0) for installed processes
        assert (0, 0) in bounds

    def test_optimize_failure_raises(self):
        """Test optimize raises RuntimeError on failure (lines 499-500)."""
        rmpo = _build_rmpo()

        with mock.patch('optimization.region_multi_period_optimization.scipy_optimize.linprog') as mock_linprog:
            mock_result = mock.MagicMock()
            mock_result.success = False
            mock_result.__str__ = lambda self: 'Failed'
            mock_linprog.return_value = mock_result

            with pytest.raises(RuntimeError, match='Region multi-period optimization failed'):
                rmpo.optimize()

    def test_shared_pool_with_group(self):
        """Test _shared_pool_availability_constraints with group (line 343)."""
        carrier = _create_mock_carrier(unit=CarrierUnit.GJ)
        installed_process = _create_mock_installed_process()
        po = mock.MagicMock()
        po.process = installed_process

        pu = _create_mock_production_unit([carrier], [po])
        # Set up a group that is different from pool
        mock_group = mock.MagicMock()
        mock_group.carrier_availability.return_value = 50.0
        pu._site.group = mock_group

        mock_region = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {
            'rolling_planning_horizon_in_years': 5,
            'year_increment': 5,
            'start_year': 2020,
            'end_year': 2025,
            'start_year_capex_factor': 1.0,
            'emission_constraint_scope': ['direct'],
            'emission_limit_in_t_co2': 1000.0,
        }
        mock_context.interest_rate = 0.05
        mock_context.co2_cost_in_euro_per_t_co2.return_value = 50.0

        rmpo = RegionMultiPeriodOptimization(2020, mock_region, [pu], mock_context)

        rows = rmpo._shared_pool_availability_constraints(0, 2020)

        # Should use pool's carrier_availability directly
        assert len(rows) == 1
        _, availability = rows[0]
        assert availability == 100.0

    def test_capacity_linking_skips_expired_capacity(self):
        """Test _capacity_linking_constraints skips prior capacity beyond lifetime (branch 381->379)."""
        # Use multiple periods with a short-lived process so that
        # year - prior_year >= lifetime for some prior periods
        carrier = _create_mock_carrier(unit=CarrierUnit.GJ)
        template_process = _create_mock_template_process(tech_available_at_year=2015)
        template_process.lifetime_in_years = 3  # Very short lifetime

        po = mock.MagicMock()
        po.process = template_process

        pu = _create_mock_production_unit([carrier], [po])

        mock_region = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {
            'rolling_planning_horizon_in_years': 15,
            'year_increment': 5,
            'start_year': 2020,
            'end_year': 2035,  # 3 periods: 2020, 2025, 2030
            'start_year_capex_factor': 1.0,
            'emission_constraint_scope': ['direct'],
            'emission_limit_in_t_co2': 1000.0,
        }
        mock_context.interest_rate = 0.05
        mock_context.co2_cost_in_euro_per_t_co2.return_value = 50.0

        rmpo = RegionMultiPeriodOptimization(2020, mock_region, [pu], mock_context)

        rows = rmpo._capacity_linking_constraints(pu)

        # With lifetime=3 and periods at 2020, 2025, 2030:
        # Period 2030: year - prior_year(2020) = 10 >= 3 (lifetime), so skip
        # This exercises the False branch at line 381
        assert len(rows) > 0

    def test_emission_budget_skips_empty_budget_years(self):
        """Test _overall_emission_budget_constraint skips periods with no budget years (line 395)."""
        carrier = _create_mock_carrier(unit=CarrierUnit.GJ)
        installed_process = _create_mock_installed_process()
        po = mock.MagicMock()
        po.process = installed_process

        pu = _create_mock_production_unit([carrier], [po])

        mock_region = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {
            'rolling_planning_horizon_in_years': 15,
            'year_increment': 5,
            'start_year': 2020,
            'end_year': 2035,  # Periods: 2020, 2025, 2030
            'start_year_capex_factor': 1.0,
            'emission_constraint_scope': ['direct'],
            'emission_limit_in_t_co2': 1000.0,
            'overall_emission_budget_in_t_co2': 5000.0,
            'emission_budget_end_year': 2022,  # Only covers first period partially
        }
        mock_context.interest_rate = 0.05
        mock_context.co2_cost_in_euro_per_t_co2.return_value = 50.0

        rmpo = RegionMultiPeriodOptimization(2020, mock_region, [pu], mock_context)

        rows = rmpo._overall_emission_budget_constraint(mock_context.simulation_options)

        # Should have 1 constraint but periods 2025 and 2030 have no budget years
        # (all years > 2022), so they are skipped (line 395)
        assert len(rows) == 1
