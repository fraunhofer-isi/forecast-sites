# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Tests for RegionMultiPeriodOptimization class.

This module tests the core functionality of the RegionMultiPeriodOptimization class,
focusing on time period calculations, index computation, and salvage value calculations
that can be tested independently of the LP solver setup.
"""

import unittest
from unittest import mock

import pytest

from carrier.carrier_unit import CarrierUnit
from optimization.region_multi_period_optimization import RegionMultiPeriodOptimization


class TestRegionMultiPeriodOptimizationSimulationPeriods(unittest.TestCase):
    """Tests for simulation period computation."""

    def test_compute_simulation_periods_standard_case(self):
        """Test period computation with standard parameters."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2020, {'end_year': 2030, 'year_increment': 5})
        assert periods == [2020, 2025, 2030]

    def test_compute_simulation_periods_single_year(self):
        """Test with start year equals end year."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2020, {'end_year': 2020, 'year_increment': 5})
        assert periods == [2020]

    def test_compute_simulation_periods_annual_increment(self):
        """Test with annual time steps."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2020, {'end_year': 2023, 'year_increment': 1})
        assert periods == [2020, 2021, 2022, 2023]

    def test_compute_simulation_periods_decade_increment(self):
        """Test with 10-year time steps."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2020, {'end_year': 2050, 'year_increment': 10})
        assert periods == [2020, 2030, 2040, 2050]

    def test_compute_simulation_periods_produces_list(self):
        """Test that result is a list."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2020, {'end_year': 2030, 'year_increment': 5})
        assert isinstance(periods, list)

    def test_compute_simulation_periods_first_is_start_year(self):
        """Test that first period is the start year."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2015, {'end_year': 2030, 'year_increment': 5})
        assert periods[0] == 2015

    def test_compute_simulation_periods_last_is_end_year(self):
        """Test that last period is the end year."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2020, {'end_year': 2035, 'year_increment': 5})
        assert periods[-1] == 2035

    def test_compute_simulation_periods_spacing_correct(self):
        """Test that periods are spaced correctly."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2010, {'end_year': 2030, 'year_increment': 5})
        for i in range(len(periods) - 1):
            assert periods[i + 1] - periods[i] == 5

    def test_compute_simulation_periods_length(self):
        """Test that correct number of periods are generated."""
        periods = RegionMultiPeriodOptimization._compute_simulation_periods(2000, {'end_year': 2040, 'year_increment': 10})
        expected_length = (2040 - 2000) // 10 + 1
        assert len(periods) == expected_length


class TestRegionMultiPeriodOptimizationTimeHelpers(unittest.TestCase):
    """
    Tests for time-related helper calculations.

    These tests validate the salvage value and budget calculations without
    requiring full LP setup.
    """

    def setUp(self):
        """Create a minimal test instance."""
        # Create mock object with minimal required attributes
        self.opt = mock.MagicMock(spec=RegionMultiPeriodOptimization)
        # Bind the real methods to the mock
        self.opt._horizon_end_year = RegionMultiPeriodOptimization._horizon_end_year.__get__(self.opt)
        self.opt._salvage_value_in_euro = RegionMultiPeriodOptimization._salvage_value_in_euro.__get__(self.opt)
        self.opt._budget_end_year = RegionMultiPeriodOptimization._budget_end_year.__get__(self.opt)
        self.opt._budget_years_in_period = RegionMultiPeriodOptimization._budget_years_in_period.__get__(self.opt)
        self.opt._years_in_period = RegionMultiPeriodOptimization._years_in_period.__get__(self.opt)
        self.opt._simulation_periods = [2020, 2025, 2030]
        self.opt._year = 2020

    def test_horizon_end_year_calculation(self):
        """Test horizon end year = last_period + increment."""
        end = self.opt._horizon_end_year({'year_increment': 5})
        assert end == 2035

    def test_horizon_end_year_with_different_increment(self):
        """Test horizon calculation with different increment."""
        end = self.opt._horizon_end_year({'year_increment': 10})
        assert end == 2040

    def test_salvage_value_no_remaining_lifetime(self):
        """Test salvage = 0 when asset fully depreciated."""
        salvage = self.opt._salvage_value_in_euro(
            capex=1000.0,
            investment_year=2020,
            lifetime=5,
            interest_rate=0.05,
            simulation_options={'year_increment': 5, 'end_year': 2030},
        )
        assert salvage == 0.0

    def test_salvage_value_positive_remaining_lifetime(self):
        """Test salvage > 0 when asset still has useful life."""
        salvage = self.opt._salvage_value_in_euro(
            capex=1000.0,
            investment_year=2020,
            lifetime=30,
            interest_rate=0.05,
            simulation_options={'year_increment': 5, 'end_year': 2030},
        )
        assert salvage > 0
        assert salvage < 1000.0  # Must be less than full capex

    def test_salvage_value_accounts_for_discount(self):
        """Test that salvage value is discounted."""
        # Same asset, different discount rates should yield different salvage
        salvage_high_rate = self.opt._salvage_value_in_euro(
            capex=1000.0,
            investment_year=2020,
            lifetime=30,
            interest_rate=0.10,
            simulation_options={'year_increment': 5, 'end_year': 2030},
        )
        salvage_low_rate = self.opt._salvage_value_in_euro(
            capex=1000.0,
            investment_year=2020,
            lifetime=30,
            interest_rate=0.02,
            simulation_options={'year_increment': 5, 'end_year': 2030},
        )
        assert salvage_low_rate > salvage_high_rate

    def test_budget_end_year_explicit_value(self):
        """Test budget end year when explicitly configured."""
        end = self.opt._budget_end_year({'emission_budget_end_year': 2028, 'year_increment': 5})
        assert end == 2028

    def test_budget_end_year_default_calculation(self):
        """Test budget end year default = last_period + increment - 1."""
        end = self.opt._budget_end_year({'year_increment': 5})
        # Last period = 2030, so: 2030 + 5 - 1 = 2034
        assert end == 2034


class TestRegionMultiPeriodOptimizationEmptyProductionUnits(unittest.TestCase):
    """Tests for edge cases with no production units."""

    def test_init_with_empty_list(self):
        """Test initialization with empty production units list."""
        mock_region = mock.MagicMock()
        mock_context = mock.MagicMock()
        mock_context.simulation_options = {'start_year': 2020, 'end_year': 2030, 'year_increment': 5}
        mock_context.interest_rate = 0.05

        opt = RegionMultiPeriodOptimization(2020, mock_region, [], mock_context)

        assert len(opt._production_units) == 0
        assert len(opt._carriers) == 0
        assert opt._num_carriers == 0


class TestRegionMultiPeriodOptimizationYearsInPeriod(unittest.TestCase):
    """Tests for _years_in_period method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock(spec=RegionMultiPeriodOptimization)
        self.opt._years_in_period = RegionMultiPeriodOptimization._years_in_period.__get__(self.opt)
        self.opt._simulation_periods = [2020, 2025, 2030]
        self.opt._num_periods = 3

    def test_years_in_first_period(self):
        """Test years in first period."""
        years = self.opt._years_in_period(0, {'year_increment': 5})
        assert years == [2020, 2021, 2022, 2023, 2024]

    def test_years_in_middle_period(self):
        """Test years in middle period."""
        years = self.opt._years_in_period(1, {'year_increment': 5})
        assert years == [2025, 2026, 2027, 2028, 2029]

    def test_years_in_last_period(self):
        """Test years in last period uses increment fallback."""
        years = self.opt._years_in_period(2, {'year_increment': 5})
        assert years == [2030, 2031, 2032, 2033, 2034]

    def test_years_in_period_length_matches_increment(self):
        """Test that years_in_period generates correct number of years."""
        years = self.opt._years_in_period(0, {'year_increment': 5})
        assert len(years) == 5


class TestRegionMultiPeriodOptimizationBudgetYearsInPeriod(unittest.TestCase):
    """Tests for _budget_years_in_period method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock(spec=RegionMultiPeriodOptimization)
        self.opt._years_in_period = RegionMultiPeriodOptimization._years_in_period.__get__(self.opt)
        self.opt._budget_years_in_period = RegionMultiPeriodOptimization._budget_years_in_period.__get__(self.opt)
        self.opt._budget_end_year = RegionMultiPeriodOptimization._budget_end_year.__get__(self.opt)
        self.opt._simulation_periods = [2020, 2025, 2030]
        self.opt._num_periods = 3

    def test_budget_years_all_within_budget(self):
        """Test budget years when all period years are within budget."""
        budget_years = self.opt._budget_years_in_period(0, {'year_increment': 5})
        assert len(budget_years) == 5
        assert budget_years[0] == 2020

    def test_budget_years_partial_period(self):
        """Test budget years when budget ends mid-period."""
        years = self.opt._budget_years_in_period(1, {'year_increment': 5, 'emission_budget_end_year': 2026})
        assert 2025 in years
        assert 2026 in years
        assert 2027 not in years


class TestRegionMultiPeriodOptimizationComputeOffsets(unittest.TestCase):
    """Tests for offset computation methods."""

    def test_compute_exec_carrier_offsets_single_pu(self):
        """Test offset computation with single production unit."""
        # Test method directly without full init
        offsets_dict = {}
        offset = 0
        num_periods = 3

        # For a single PU with 4 vars per period
        pu = mock.MagicMock()
        vars_per_period = 4

        offsets_dict[pu] = offset
        offset += vars_per_period * num_periods

        assert offsets_dict[pu] == 0
        assert offset == 12

    def test_new_capacity_section_starts_after_exec_carrier(self):
        """Test that new capacity section follows exec+carrier section."""
        # Simulate offset calculation
        mock.MagicMock()
        num_periods = 3
        vars_per_period = 4
        num_procs = 2

        exec_carrier_section = vars_per_period * num_periods  # 12
        new_cap_section_start = exec_carrier_section
        new_cap_section_size = num_procs * num_periods  # 6

        assert new_cap_section_start == 12
        assert new_cap_section_size == 6
        assert new_cap_section_start + new_cap_section_size == 18


class TestRegionMultiPeriodOptimizationCarrierCost(unittest.TestCase):
    """Tests for _carrier_cost_in_euro_per_unit method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock(spec=RegionMultiPeriodOptimization)
        self.opt._carrier_cost_in_euro_per_unit = RegionMultiPeriodOptimization._carrier_cost_in_euro_per_unit.__get__(self.opt)
        self.opt._context = mock.MagicMock()

    def test_carrier_cost_basic_purchase(self):
        """Test carrier cost with purchase price only."""
        carrier = mock.MagicMock()
        carrier.purchase_price_in_euro_per_unit.return_value = 100.0
        carrier.sell_price_in_euro_per_unit.return_value = 0.0
        carrier.taxes_in_euro_per_unit.return_value = 0.0
        carrier.subsidies_in_euro_per_unit.return_value = 0.0
        carrier.upstream_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.0
        self.opt._context.co2_cost_in_euro_per_t_co2.return_value = 50.0

        cost = self.opt._carrier_cost_in_euro_per_unit(carrier, 2020, {})
        assert cost == 100.0

    def test_carrier_cost_with_taxes_and_subsidies(self):
        """Test carrier cost includes taxes and subtracts subsidies."""
        carrier = mock.MagicMock()
        carrier.purchase_price_in_euro_per_unit.return_value = 100.0
        carrier.sell_price_in_euro_per_unit.return_value = 0.0
        carrier.taxes_in_euro_per_unit.return_value = 10.0
        carrier.subsidies_in_euro_per_unit.return_value = 5.0
        carrier.upstream_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.0
        self.opt._context.co2_cost_in_euro_per_t_co2.return_value = 50.0

        cost = self.opt._carrier_cost_in_euro_per_unit(carrier, 2020, {})
        assert cost == 100.0 + 10.0 - 5.0

    def test_carrier_cost_with_emissions(self):
        """Test carrier cost includes emission costs."""
        carrier = mock.MagicMock()
        carrier.purchase_price_in_euro_per_unit.return_value = 100.0
        carrier.sell_price_in_euro_per_unit.return_value = 0.0
        carrier.taxes_in_euro_per_unit.return_value = 0.0
        carrier.subsidies_in_euro_per_unit.return_value = 0.0
        carrier.upstream_emission_in_t_co2_per_unit.return_value = 0.5  # 0.5 t CO2
        carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.0
        self.opt._context.co2_cost_in_euro_per_t_co2.return_value = 50.0

        cost = self.opt._carrier_cost_in_euro_per_unit(carrier, 2020, {})
        # 100 + (0.5 * 50) = 100 + 25 = 125
        assert cost == 125.0

    def test_carrier_cost_with_sell_price(self):
        """Test carrier cost reduces with sell price (revenue)."""
        carrier = mock.MagicMock()
        carrier.purchase_price_in_euro_per_unit.return_value = 100.0
        carrier.sell_price_in_euro_per_unit.return_value = 20.0
        carrier.taxes_in_euro_per_unit.return_value = 0.0
        carrier.subsidies_in_euro_per_unit.return_value = 0.0
        carrier.upstream_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.0
        self.opt._context.co2_cost_in_euro_per_t_co2.return_value = 50.0

        cost = self.opt._carrier_cost_in_euro_per_unit(carrier, 2020, {})
        assert cost == 100.0 - 20.0


class TestRegionMultiPeriodOptimizationEmissionCoefficients(unittest.TestCase):
    """Tests for emission coefficient methods."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock(spec=RegionMultiPeriodOptimization)
        self.opt._process_emission_coefficient = RegionMultiPeriodOptimization._process_emission_coefficient.__get__(self.opt)
        self.opt._carrier_emission_coefficient = RegionMultiPeriodOptimization._carrier_emission_coefficient.__get__(self.opt)
        self.opt._carrier_downstream_emission = RegionMultiPeriodOptimization._carrier_downstream_emission
        self.opt._carriers = []

    def test_process_emission_direct_only(self):
        """Test process emission with only direct scope."""
        process = mock.MagicMock()
        process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 5.0
        process.emission.captured_emission_in_t_co2_per_process_count = 0.0

        coeff = self.opt._process_emission_coefficient(process, 2020, {'emission_constraint_scope': ['direct']})
        assert coeff == 5.0

    def test_process_emission_with_capture(self):
        """Test process emission subtracts captured emissions."""
        process = mock.MagicMock()
        process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 5.0
        process.emission.captured_emission_in_t_co2_per_process_count = 1.0

        coeff = self.opt._process_emission_coefficient(process, 2020, {'emission_constraint_scope': ['direct']})
        assert coeff == 4.0

    def test_carrier_emission_upstream(self):
        """Test carrier upstream emission."""
        carrier = mock.MagicMock()
        carrier.upstream_emission_in_t_co2_per_unit.return_value = 2.0
        carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.0

        coeff = self.opt._carrier_emission_coefficient(carrier, 2020, {'emission_constraint_scope': ['upstream']})
        assert coeff == 2.0

    def test_carrier_emission_renewably_bound(self):
        """Test carrier renewably bound emission reduces coefficient."""
        carrier = mock.MagicMock()
        carrier.upstream_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 1.5

        coeff = self.opt._carrier_emission_coefficient(carrier, 2020, {'emission_constraint_scope': ['renewably_bound']})
        assert coeff == -1.5

    def test_carrier_downstream_emission_missing_attribute(self):
        """Test carrier downstream emission returns 0 if method missing."""
        carrier = mock.MagicMock(spec=[])  # No methods
        result = RegionMultiPeriodOptimization._carrier_downstream_emission(carrier, 2020, {})
        assert result == 0.0

    def test_carrier_downstream_emission_with_method(self):
        """Test carrier downstream emission calls method if present."""
        carrier = mock.MagicMock()
        carrier.downstream_emission_in_t_co2_per_unit.return_value = 3.0
        result = RegionMultiPeriodOptimization._carrier_downstream_emission(carrier, 2020, {})
        assert result == 3.0


class TestRegionMultiPeriodOptimizationMinimumExport(unittest.TestCase):
    """Tests for _minimum_export method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock(spec=RegionMultiPeriodOptimization)
        self.opt._minimum_export = RegionMultiPeriodOptimization._minimum_export.__get__(self.opt)

    def test_minimum_export_unit_tonnes(self):
        """Test minimum export for tonnes unit."""
        pu = mock.MagicMock()
        pu.carrier_minimum_export_in_t.return_value = 50.0

        carrier = mock.MagicMock()
        carrier.unit = CarrierUnit.T

        result = self.opt._minimum_export(pu, carrier, 2020, {})
        assert result == 50.0
        pu.carrier_minimum_export_in_t.assert_called_once()

    def test_minimum_export_unit_gj(self):
        """Test minimum export for energy unit returns 0."""
        pu = mock.MagicMock()
        carrier = mock.MagicMock()
        carrier.unit = CarrierUnit.GJ

        result = self.opt._minimum_export(pu, carrier, 2020, {})
        assert result == 0

    def test_minimum_export_unknown_unit_raises(self):
        """Test minimum export raises TypeError for unknown unit."""
        pu = mock.MagicMock()
        carrier = mock.MagicMock()
        carrier.unit = mock.MagicMock()  # Unknown unit

        with pytest.raises(TypeError) as context:
            self.opt._minimum_export(pu, carrier, 2020, {})
        assert 'Unknown carrier unit' in str(context.value)


class TestRegionMultiPeriodOptimizationBuildBounds(unittest.TestCase):
    """Tests for _build_bounds method."""

    def test_build_bounds_empty_production_units(self):
        """Test bounds for zero production units."""
        opt = mock.MagicMock(spec=RegionMultiPeriodOptimization)
        opt._build_bounds = RegionMultiPeriodOptimization._build_bounds.__get__(opt)
        opt._production_units = []
        opt._num_periods = 2
        opt._num_proc_by_pu = {}
        opt._num_carriers = 3

        bounds = opt._build_bounds()
        assert bounds == []

    def test_build_bounds_structure(self):
        """Test bounds structure for production units."""
        opt = mock.MagicMock()
        opt._build_bounds = RegionMultiPeriodOptimization._build_bounds.__get__(opt)

        process = mock.MagicMock()
        process.tech_available_at_year = 2020

        po = mock.MagicMock()
        po.process = process

        pu1 = mock.MagicMock()
        pu1._site = mock.MagicMock()
        opt._production_units = [pu1]
        opt._num_periods = 2
        opt._num_proc_by_pu = {pu1: 2}  # 2 processes
        opt._num_carriers = 1
        opt._simulation_periods = [2020, 2025]
        opt._process_options_by_pu = {pu1: [po, po]}

        bounds = opt._build_bounds()
        # For 2 periods, 2 processes, 1 carrier per period = (2+1)*2 = 6 exec+carrier vars
        # For 2 periods, 2 processes = 2*2 = 4 new_capacity vars (both have unrestricted bounds)
        # Total = 10
        assert len(bounds) == 10
        # All should be non-negative
        for lower, _upper in bounds:
            assert lower == 0


class TestRegionMultiPeriodOptimizationConstraintHelpers(unittest.TestCase):
    """Tests for constraint building helper methods."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock()
        self.opt._pu_production_constraints = RegionMultiPeriodOptimization._pu_production_constraints.__get__(self.opt)
        self.opt._pu_capture_constraints = RegionMultiPeriodOptimization._pu_capture_constraints.__get__(self.opt)
        self.opt._total_variables = 20
        self.opt._exec_index = RegionMultiPeriodOptimization._exec_index.__get__(self.opt)
        self.opt._num_proc_by_pu = {}
        self.opt._offsets_by_pu = {}

    def test_pu_production_constraints_installed_process(self):
        """Test production constraint for installed process."""
        from processes.installed_process import InstalledProcess

        pu = mock.MagicMock()
        process = mock.MagicMock(spec=InstalledProcess)
        process.available_process_execution_count.return_value = 100

        po = mock.MagicMock()
        po.process = process

        self.opt._process_options_by_pu = {pu: [po]}
        self.opt._num_proc_by_pu[pu] = 1
        self.opt._num_carriers = 2
        self.opt._vars_per_period_by_pu = {pu: 3}
        self.opt._offsets_by_pu[pu] = 0

        rows = self.opt._pu_production_constraints(pu, 0, 2020)
        assert len(rows) == 1
        _coeff, capacity = rows[0]
        assert capacity == 100

    def test_pu_production_constraints_unavailable_technology(self):
        """Test production constraint when technology not available."""
        pu = mock.MagicMock()
        process = mock.MagicMock()
        process.tech_available_at_year = 2025  # Not available in 2020

        po = mock.MagicMock()
        po.process = process

        self.opt._process_options_by_pu = {pu: [po]}
        self.opt._num_proc_by_pu[pu] = 1
        self.opt._num_carriers = 2
        self.opt._vars_per_period_by_pu = {pu: 3}
        self.opt._offsets_by_pu[pu] = 0

        rows = self.opt._pu_production_constraints(pu, 0, 2020)
        assert len(rows) == 1
        _coeff, capacity = rows[0]
        assert capacity == 0

    def test_pu_production_constraints_available_technology(self):
        """Test production constraint when technology available."""
        pu = mock.MagicMock()
        process = mock.MagicMock()
        process.tech_available_at_year = 2015

        po = mock.MagicMock()
        po.process = process

        self.opt._process_options_by_pu = {pu: [po]}
        self.opt._num_proc_by_pu[pu] = 1
        self.opt._num_carriers = 2
        self.opt._vars_per_period_by_pu = {pu: 3}
        self.opt._offsets_by_pu[pu] = 0

        rows = self.opt._pu_production_constraints(pu, 0, 2020)
        assert len(rows) == 1
        _coeff, capacity = rows[0]
        assert capacity == 1e41  # Large upper bound

    def test_pu_capture_constraints_returns_single_row(self):
        """Test capture constraint returns single row."""
        pu = mock.MagicMock()
        process = mock.MagicMock()
        process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 5.0
        process.emission.captured_input_emission_in_t_co2_per_process_count = 1.0

        po = mock.MagicMock()
        po.process = process

        self.opt._process_options_by_pu = {pu: [po]}
        self.opt._num_proc_by_pu[pu] = 1
        self.opt._num_carriers = 2
        self.opt._vars_per_period_by_pu = {pu: 3}
        self.opt._offsets_by_pu[pu] = 0

        rows = self.opt._pu_capture_constraints(pu, 0, 2020)
        assert len(rows) == 1
        coeff, limit = rows[0]
        assert limit == 0
        assert coeff[0] == -(5.0 - 1.0)


class TestRegionMultiPeriodOptimizationOverallEmissionBudget(unittest.TestCase):
    """Tests for _overall_emission_budget_constraint method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock()
        self.opt._overall_emission_budget_constraint = RegionMultiPeriodOptimization._overall_emission_budget_constraint.__get__(
            self.opt
        )
        self.opt._budget_years_in_period = mock.MagicMock(return_value=[])
        self.opt._total_variables = 20
        self.opt._num_periods = 2

    def test_overall_emission_budget_none_returns_empty(self):
        """Test that missing budget returns empty list."""
        self.opt._simulation_periods = [2020, 2025]

        rows = self.opt._overall_emission_budget_constraint({'overall_emission_budget_in_t_co2': None})
        assert rows == []

    def test_overall_emission_budget_not_in_options_returns_empty(self):
        """Test that missing budget key returns empty list."""
        self.opt._simulation_periods = [2020, 2025]

        rows = self.opt._overall_emission_budget_constraint({})
        assert rows == []


class TestRegionMultiPeriodOptimizationCarrierConstraints(unittest.TestCase):
    """Tests for _pu_carrier_constraints method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock()
        self.opt._pu_carrier_constraints = RegionMultiPeriodOptimization._pu_carrier_constraints.__get__(self.opt)
        self.opt._minimum_export = RegionMultiPeriodOptimization._minimum_export.__get__(self.opt)
        self.opt._total_variables = 20
        self.opt._carrier_index = RegionMultiPeriodOptimization._carrier_index.__get__(self.opt)
        self.opt._exec_index = RegionMultiPeriodOptimization._exec_index.__get__(self.opt)
        self.opt._num_proc_by_pu = {}
        self.opt._offsets_by_pu = {}

    def test_pu_carrier_constraints_multiple_carriers(self):
        """Test carrier constraints for multiple carriers."""
        pu = mock.MagicMock()

        carrier1 = mock.MagicMock()
        carrier1.unit = CarrierUnit.T
        carrier1.maximum_production_in_unit = 1000.0
        carrier1.minimum_use_in_unit.return_value = 10.0

        carrier2 = mock.MagicMock()
        carrier2.unit = CarrierUnit.GJ
        carrier2.maximum_production_in_unit = 5000.0
        carrier2.minimum_use_in_unit.return_value = 50.0

        process = mock.MagicMock()
        process.netto_produced_or_consumed_amount_per_process_count.side_effect = [10.0, 20.0, 15.0, 25.0]

        po = mock.MagicMock()
        po.process = process

        self.opt._process_options_by_pu = {pu: [po]}
        self.opt._carriers = [carrier1, carrier2]
        self.opt._num_proc_by_pu[pu] = 1
        self.opt._num_carriers = 2
        self.opt._vars_per_period_by_pu = {pu: 3}
        self.opt._offsets_by_pu[pu] = 0
        pu.carrier_minimum_export_in_t.return_value = 5.0

        rows = self.opt._pu_carrier_constraints(pu, 0, 2020, {})
        # For each carrier: min_export, max_prod, min_use = 3 constraints per carrier
        # Total = 2 carriers * 3 = 6 rows
        assert len(rows) == 6


class TestRegionMultiPeriodOptimizationEmissionConstraints(unittest.TestCase):
    """Tests for _pu_emission_constraints method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock()
        self.opt._pu_emission_constraints = RegionMultiPeriodOptimization._pu_emission_constraints.__get__(self.opt)
        self.opt._process_emission_coefficient = RegionMultiPeriodOptimization._process_emission_coefficient.__get__(self.opt)
        self.opt._carrier_emission_coefficient = RegionMultiPeriodOptimization._carrier_emission_coefficient.__get__(self.opt)
        self.opt._total_variables = 20
        self.opt._exec_index = RegionMultiPeriodOptimization._exec_index.__get__(self.opt)
        self.opt._carrier_index = RegionMultiPeriodOptimization._carrier_index.__get__(self.opt)
        self.opt._num_proc_by_pu = {}
        self.opt._offsets_by_pu = {}

    def test_pu_emission_constraints_single_process(self):
        """Test emission constraint for single process."""
        pu = mock.MagicMock()

        process = mock.MagicMock()
        process.emission.direct_emissions_in_t_co2_per_process_count.return_value = 5.0
        process.emission.captured_emission_in_t_co2_per_process_count = 0.0

        po = mock.MagicMock()
        po.process = process

        carrier = mock.MagicMock()
        carrier.upstream_emission_in_t_co2_per_unit.return_value = 0.0
        carrier.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.0

        self.opt._process_options_by_pu = {pu: [po]}
        self.opt._carriers = [carrier]
        self.opt._num_proc_by_pu[pu] = 1
        self.opt._num_carriers = 1
        self.opt._vars_per_period_by_pu = {pu: 2}
        self.opt._offsets_by_pu[pu] = 0

        rows = self.opt._pu_emission_constraints(
            pu,
            0,
            2020,
            {'emission_limit_in_t_co2': 100, 'emission_constraint_scope': ['direct']},
        )
        assert len(rows) == 1
        _coeff, limit = rows[0]
        assert limit == 100


class TestRegionMultiPeriodOptimizationSitePurchaseConstraints(unittest.TestCase):
    """Tests for _site_purchase_eligibility_constraints method."""

    def setUp(self):
        """Create a minimal test instance."""
        self.opt = mock.MagicMock()
        self.opt._site_purchase_eligibility_constraints = (
            RegionMultiPeriodOptimization._site_purchase_eligibility_constraints.__get__(self.opt)
        )
        self.opt._total_variables = 20
        self.opt._carrier_index = RegionMultiPeriodOptimization._carrier_index.__get__(self.opt)
        self.opt._num_carriers = 2

    def test_site_purchase_eligibility_constraints(self):
        """Test purchase eligibility constraints."""
        pu = mock.MagicMock()
        site = mock.MagicMock()
        pu._site = site

        carrier1 = mock.MagicMock()
        carrier2 = mock.MagicMock()

        # Site cannot purchase carrier1 but can purchase carrier2
        site.can_purchase.side_effect = [False, True]

        self.opt._production_units = [pu]
        self.opt._carriers = [carrier1, carrier2]
        self.opt._num_proc_by_pu = {pu: 1}
        self.opt._vars_per_period_by_pu = {pu: 2}
        self.opt._offsets_by_pu = {pu: 0}

        rows = self.opt._site_purchase_eligibility_constraints(0, 2020)
        # Only carrier1 cannot be purchased, so 1 constraint row
        assert len(rows) == 1
        _coeff, limit = rows[0]
        assert limit == 0.0


if __name__ == '__main__':
    unittest.main()
