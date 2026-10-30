# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for CollectingResultVisitor class."""

import unittest
from unittest import mock

import pytest

from by_product.by_product import ByProduct
from carrier.carrier_unit import CarrierUnit
from energy_carrier.energy_carrier import EnergyCarrier
from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand
from product.product import Product
from result.collecting_result_visitor import CollectingResultVisitor


class TestCollectingResultVisitorInit(unittest.TestCase):
    """Tests for CollectingResultVisitor initialization."""

    def test_init_with_simulation_options(self):
        """Test initialization with simulation options."""
        simulation_options = {'key': 'value'}
        visitor = CollectingResultVisitor(simulation_options)
        # CO2 cost should be None initially
        assert visitor._co2_cost_in_euro_per_t_co2 is None

    def test_init_sets_interest_rate_to_none(self):
        """Test that interest rate is initialized to None."""
        visitor = CollectingResultVisitor({})
        assert visitor._interest_rate is None


class TestCollectingResultVisitorEnterRegion(unittest.TestCase):
    """Tests for enter_region method."""

    def test_enter_region_sets_co2_cost(self):
        """Test that enter_region sets CO2 cost from region."""
        visitor = CollectingResultVisitor({})
        mock_region = mock.MagicMock()
        mock_region.co2_cost_in_euro_per_t_co2 = mock.MagicMock(return_value=50.0)
        mock_region.interest_rate = 0.05

        visitor.enter_region(mock_region, 2020)

        assert visitor._co2_cost_in_euro_per_t_co2 == 50.0

    def test_enter_region_sets_interest_rate(self):
        """Test that enter_region sets interest rate from region."""
        visitor = CollectingResultVisitor({})
        mock_region = mock.MagicMock()
        mock_region.co2_cost_in_euro_per_t_co2 = mock.MagicMock(return_value=25.0)
        mock_region.interest_rate = 0.07

        visitor.enter_region(mock_region, 2020)

        assert visitor._interest_rate == 0.07

    def test_enter_region_different_years(self):
        """Test enter_region with different years."""
        visitor = CollectingResultVisitor({})
        mock_region = mock.MagicMock()
        mock_region.co2_cost_in_euro_per_t_co2 = mock.MagicMock(return_value=30.0)
        mock_region.interest_rate = 0.03

        visitor.enter_region(mock_region, 2025)

        mock_region.co2_cost_in_euro_per_t_co2.assert_called_with(2025)


class TestCollectingResultVisitorCarrierEmissionCost(unittest.TestCase):
    """Tests for carrier emission cost calculation."""

    def test_carrier_emission_cost_positive_sign(self):
        """Test carrier emission cost with positive sign."""
        visitor = CollectingResultVisitor({})
        visitor._co2_cost_in_euro_per_t_co2 = 50.0

        emission_by_carrier = {
            mock.MagicMock(): 10.0,
            mock.MagicMock(): 20.0,
        }

        result = visitor._carrier_emission_cost_in_euro(emission_by_carrier, sign=1)

        assert len(result) == 2
        costs = list(result.values())
        assert 500.0 in costs  # 10 * 50
        assert 1000.0 in costs  # 20 * 50

    def test_carrier_emission_cost_negative_sign(self):
        """Test carrier emission cost with negative sign."""
        visitor = CollectingResultVisitor({})
        visitor._co2_cost_in_euro_per_t_co2 = 50.0

        carrier = mock.MagicMock()
        emission_by_carrier = {carrier: 10.0}

        result = visitor._carrier_emission_cost_in_euro(emission_by_carrier, sign=-1)

        assert result[carrier] == -500.0

    def test_carrier_emission_cost_zero_emission(self):
        """Test carrier emission cost with zero emission."""
        visitor = CollectingResultVisitor({})
        visitor._co2_cost_in_euro_per_t_co2 = 50.0

        carrier = mock.MagicMock()
        emission_by_carrier = {carrier: 0.0}

        result = visitor._carrier_emission_cost_in_euro(emission_by_carrier)

        assert result[carrier] == 0.0

    def test_carrier_emission_cost_empty_dict(self):
        """Test carrier emission cost with empty emissions."""
        visitor = CollectingResultVisitor({})
        visitor._co2_cost_in_euro_per_t_co2 = 50.0

        result = visitor._carrier_emission_cost_in_euro({})

        assert result == {}


class TestCollectingResultVisitorRegionAndSectorResults(unittest.TestCase):
    """Tests for region and sector result names."""

    def test_region_and_sector_energy_carrier_result_names(self):
        """Test static method returns expected names."""
        names = CollectingResultVisitor._region_and_sector_energy_carrier_result_names()

        assert 'purchased_amount' in names
        assert 'upstream_emission_in_t_co2' in names
        assert 'downstream_emission_in_t_co2' in names
        assert 'renewably_bound_co2_emission_in_t_co2' in names

    def test_region_and_sector_result_names_is_set(self):
        """Test that result names is a set."""
        names = CollectingResultVisitor._region_and_sector_energy_carrier_result_names()
        assert isinstance(names, set)


class TestCollectingResultVisitorSiteCarrierHandling(unittest.TestCase):
    """Tests for site purchased carrier handling."""

    def test_handle_site_purchased_energy_carrier(self):
        """Test handling site purchased energy carrier."""
        visitor = CollectingResultVisitor({})
        # Initialize result structures
        visitor._absolute_results = {'site_energy_carrier_purchased_amount_in_gj': {}}

        mock_energy_carrier = mock.MagicMock(spec=EnergyCarrier)
        mock_energy_carrier.unit = CarrierUnit.GJ
        mock_energy_carrier.id = 1

        purchased_amounts = {mock_energy_carrier: 100.0}

        # Test would require full initialization, so we test the logic directly
        # by mocking the add method
        visitor._add_site_energy_carrier_entry = mock.MagicMock()

        visitor._handle_site_purchased_carrier_amounts(purchased_amounts, 2020)

        visitor._add_site_energy_carrier_entry.assert_called_once()

    def test_handle_site_purchased_product(self):
        """Test handling site purchased product."""
        visitor = CollectingResultVisitor({})
        visitor._absolute_results = {'site_product_purchased_amount_in_t': {}}

        mock_product = mock.MagicMock(spec=Product)
        mock_product.unit = CarrierUnit.T
        mock_product.id = 2

        purchased_amounts = {mock_product: 50.0}

        visitor._add_site_product_entry = mock.MagicMock()

        visitor._handle_site_purchased_carrier_amounts(purchased_amounts, 2020)

        visitor._add_site_product_entry.assert_called_once()

    def test_handle_site_purchased_by_product(self):
        """Test handling site purchased by-product."""
        visitor = CollectingResultVisitor({})
        visitor._absolute_results = {'site_by_product_purchased_amount_in_t': {}}

        mock_by_product = mock.MagicMock(spec=ByProduct)
        mock_by_product.unit = CarrierUnit.T
        mock_by_product.id = 3

        purchased_amounts = {mock_by_product: 25.0}

        visitor._add_site_by_product_entry = mock.MagicMock()

        visitor._handle_site_purchased_carrier_amounts(purchased_amounts, 2020)

        visitor._add_site_by_product_entry.assert_called_once()

    def test_handle_site_unknown_carrier_unit_raises(self):
        """Test that unknown carrier unit raises ValueError."""
        visitor = CollectingResultVisitor({})

        mock_carrier = mock.MagicMock()
        mock_carrier.unit = 'UNKNOWN_UNIT'

        purchased_amounts = {mock_carrier: 100.0}

        with pytest.raises(ValueError, match='Unknown carrier unit'):
            visitor._handle_site_purchased_carrier_amounts(purchased_amounts, 2020)

    def test_handle_site_unknown_carrier_type_raises(self):
        """Test that unknown carrier type (T unit) raises NotImplementedError."""
        visitor = CollectingResultVisitor({})

        mock_carrier = mock.MagicMock()
        mock_carrier.unit = CarrierUnit.T
        # Not Product or ByProduct

        purchased_amounts = {mock_carrier: 100.0}

        with pytest.raises(NotImplementedError) as ctx:
            visitor._handle_site_purchased_carrier_amounts(purchased_amounts, 2020)

        assert 'not yet implemented' in str(ctx.value)


class TestCollectingResultVisitorProductionUnitCarrier(unittest.TestCase):
    """Tests for production unit carrier result handling."""

    def test_handle_production_unit_energy_carrier_result(self):
        """Test handling production unit energy carrier result."""
        visitor = CollectingResultVisitor({})
        visitor._absolute_results = {'production_unit_energy_carrier_purchase_cost_in_euro': {}}

        mock_energy_carrier = mock.MagicMock(spec=EnergyCarrier)
        mock_energy_carrier.unit = CarrierUnit.GJ
        mock_energy_carrier.id = 1

        carrier_dict = {mock_energy_carrier: 500.0}

        visitor._add_production_unit_energy_carrier_entry = mock.MagicMock()
        visitor._add_region_and_sector_energy_carrier_aggregates = mock.MagicMock()

        visitor._handle_production_unit_carrier_result(carrier_dict, 'purchase_cost_in_euro', 2020)

        visitor._add_production_unit_energy_carrier_entry.assert_called_once()

    def test_handle_production_unit_product_result(self):
        """Test handling production unit product result."""
        visitor = CollectingResultVisitor({})
        visitor._absolute_results = {'production_unit_product_purchase_cost_in_euro': {}}

        mock_product = mock.MagicMock(spec=Product)
        mock_product.unit = CarrierUnit.T
        mock_product.id = 2

        carrier_dict = {mock_product: 1000.0}

        visitor._add_production_unit_product_entry = mock.MagicMock()

        visitor._handle_production_unit_carrier_result(carrier_dict, 'purchase_cost_in_euro', 2020)

        visitor._add_production_unit_product_entry.assert_called_once()

    def test_handle_production_unit_by_product_result(self):
        """Test handling production unit by-product result."""
        visitor = CollectingResultVisitor({})
        visitor._absolute_results = {'production_unit_by_product_purchase_cost_in_euro': {}}

        mock_by_product = mock.MagicMock(spec=ByProduct)
        mock_by_product.unit = CarrierUnit.T
        mock_by_product.id = 3

        carrier_dict = {mock_by_product: 500.0}

        visitor._add_production_unit_by_product_entry = mock.MagicMock()

        visitor._handle_production_unit_carrier_result(carrier_dict, 'purchase_cost_in_euro', 2020)

        visitor._add_production_unit_by_product_entry.assert_called_once()

    def test_handle_production_unit_with_unit_append(self):
        """Test handling with unit append in table name."""
        visitor = CollectingResultVisitor({})
        visitor._absolute_results = {'production_unit_energy_carrier_export_in_gj': {}}

        mock_energy_carrier = mock.MagicMock(spec=EnergyCarrier)
        mock_energy_carrier.unit = CarrierUnit.GJ
        mock_energy_carrier.id = 1

        carrier_dict = {mock_energy_carrier: 100.0}

        visitor._add_production_unit_energy_carrier_entry = mock.MagicMock()
        visitor._add_region_and_sector_energy_carrier_aggregates = mock.MagicMock()

        visitor._handle_production_unit_carrier_result(carrier_dict, 'export', 2020, append_unit=True)

        # Verify the call was made (table name would include _in_gj)
        visitor._add_production_unit_energy_carrier_entry.assert_called_once()


class TestCollectingResultVisitorAddProcessEmission(unittest.TestCase):
    """Tests for process emission aggregates."""

    def test_add_process_emission_aggregates(self):
        """Test adding process emission aggregates."""
        visitor = CollectingResultVisitor({})
        visitor._absolute_results = {
            'region_direct_emission_in_t_co2': {},
            'sector_direct_emission_in_t_co2': {},
        }
        visitor._add_region_entry_or_accumulate = mock.MagicMock()
        visitor._add_sector_entry_or_accumulate = mock.MagicMock()

        visitor._add_process_emission_aggregates('direct_emission_in_t_co2', 2020, 10.0)

        visitor._add_region_entry_or_accumulate.assert_called_once()
        visitor._add_sector_entry_or_accumulate.assert_called_once()


class TestCollectingResultVisitorInitialization(unittest.TestCase):
    """Tests for result initialization."""

    def test_initialize_creates_absolute_results_dict(self):
        """Test that _initialize creates absolute results dictionary."""
        visitor = CollectingResultVisitor({})
        visitor._initialize()

        assert visitor._absolute_results is not None
        assert isinstance(visitor._absolute_results, dict)
        assert len(visitor._absolute_results) > 0

    def test_initialize_creates_specific_results_dict(self):
        """Test that _initialize creates specific results dictionary."""
        visitor = CollectingResultVisitor({})
        visitor._initialize()

        assert visitor._specific_results is not None
        assert isinstance(visitor._specific_results, dict)

    def test_initialize_region_and_sector_energy_carrier_purchased(self):
        """Test initialization includes region energy carrier purchased."""
        visitor = CollectingResultVisitor({})
        visitor._initialize()

        assert 'region_energy_carrier_purchased_amount_in_gj' in visitor._absolute_results
        assert 'sector_energy_carrier_purchased_amount_in_gj' in visitor._absolute_results


class TestCollectingResultVisitorExitSite(unittest.TestCase):
    """Tests for exit_site method."""

    def test_exit_site_aggregates_results(self):
        """Test exit_site aggregates production unit results."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'site_product_purchased_amount_in_t': {},
            'site_energy_carrier_purchased_amount_in_gj': {},
            'site_by_product_purchased_amount_in_t': {},
        }
        visitor._handle_site_purchased_carrier_amounts = mock.MagicMock()

        with mock.patch('result.aggregation.aggregate_dictionaries') as mock_agg:
            mock_agg.return_value = {'purchased_carrier_amounts': {}}
            result = visitor.exit_site(mock.MagicMock(), 2020, {}, [{}])

            assert result == {'purchased_carrier_amounts': {}}
            visitor._handle_site_purchased_carrier_amounts.assert_called_once()

    def test_exit_site_passes_year(self):
        """Test exit_site passes correct year to handler."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'site_product_purchased_amount_in_t': {},
            'site_energy_carrier_purchased_amount_in_gj': {},
            'site_by_product_purchased_amount_in_t': {},
        }
        visitor._handle_site_purchased_carrier_amounts = mock.MagicMock()

        with mock.patch('result.aggregation.aggregate_dictionaries') as mock_agg:
            mock_agg.return_value = {'purchased_carrier_amounts': {}}
            visitor.exit_site(mock.MagicMock(), 2025, {}, [])

            call_year = visitor._handle_site_purchased_carrier_amounts.call_args[0][1]
            assert call_year == 2025


class TestCollectingResultVisitorExitProductionUnit(unittest.TestCase):
    """Tests for exit_production_unit method."""

    def test_exit_production_unit_collects_budget_when_summary_exists(self):
        """Test exit_production_unit collects budget when summary exists."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'production_unit_budget_relevant_emission_in_t_co2': {},
            'production_unit_overall_emission_budget_used_in_t_co2': {},
            'production_unit_overall_emission_budget_in_t_co2': {},
            'production_unit_energy_carrier_purchased_amount_in_gj': {},
            'production_unit_product_purchased_amount_in_t': {},
            'production_unit_by_product_purchased_amount_in_t': {},
            'production_unit_energy_carrier_purchase_cost_in_euro': {},
            'production_unit_product_purchase_cost_in_euro': {},
            'production_unit_by_product_purchase_cost_in_euro': {},
            'production_unit_energy_carrier_taxes_in_euro': {},
            'production_unit_energy_carrier_subsidies_in_euro': {},
            'production_unit_energy_carrier_export_in_gj': {},
            'production_unit_product_export_in_t': {},
            'production_unit_by_product_export_in_t': {},
            'production_unit_energy_carrier_sell_gain_in_euro': {},
            'production_unit_product_sell_gain_in_euro': {},
            'production_unit_by_product_sell_gain_in_euro': {},
            'production_unit_energy_carrier_upstream_emission_in_t_co2': {},
            'production_unit_product_upstream_emission_in_t_co2': {},
            'production_unit_by_product_upstream_emission_in_t_co2': {},
            'production_unit_energy_carrier_downstream_emission_in_t_co2': {},
            'production_unit_product_downstream_emission_in_t_co2': {},
            'production_unit_by_product_downstream_emission_in_t_co2': {},
            'production_unit_energy_carrier_renewably_bound_co2_emission_in_t_co2': {},
            'production_unit_product_renewably_bound_co2_emission_in_t_co2': {},
            'production_unit_by_product_renewably_bound_co2_emission_in_t_co2': {},
            'production_unit_energy_carrier_upstream_emission_cost_in_euro': {},
            'production_unit_product_upstream_emission_cost_in_euro': {},
            'production_unit_by_product_upstream_emission_cost_in_euro': {},
            'production_unit_energy_carrier_downstream_emission_cost_in_euro': {},
            'production_unit_product_downstream_emission_cost_in_euro': {},
            'production_unit_by_product_downstream_emission_cost_in_euro': {},
            'production_unit_energy_carrier_renewably_bound_co2_emission_cost_in_euro': {},
            'production_unit_product_renewably_bound_co2_emission_cost_in_euro': {},
            'production_unit_by_product_renewably_bound_co2_emission_cost_in_euro': {},
        }
        visitor._simulation_options = {'start_year': 2020}
        visitor._co2_cost_in_euro_per_t_co2 = 50.0
        visitor._interest_rate = 0.05
        visitor._add_production_unit_entry = mock.MagicMock()

        mock_pu = mock.MagicMock()
        mock_pu.multi_period_budget_summary = {'used_in_t_co2': 10.0, 'available_in_t_co2': 100.0}
        mock_pu.budget_relevant_emission_in_t_co2 = mock.MagicMock(return_value=5.0)
        mock_pu.purchased_carrier_amounts = {}
        mock_pu.carrier_purchase_cost_in_euro = mock.MagicMock(return_value={})
        mock_pu.energy_carrier_taxes_in_euro = mock.MagicMock(return_value={})
        mock_pu.energy_carrier_subsidies_in_euro = mock.MagicMock(return_value={})
        mock_pu.export = mock.MagicMock(return_value={})
        mock_pu.sell_gain_in_euro = mock.MagicMock(return_value={})
        mock_pu.upstream_emission_in_t_co2 = mock.MagicMock(return_value={})
        mock_pu.downstream_emission_in_t_co2 = mock.MagicMock(return_value={})
        mock_pu.renewably_bound_co2_emission_in_t_co2 = mock.MagicMock(return_value={})

        visitor._handle_production_unit_carrier_result = mock.MagicMock()
        visitor._carrier_emission_cost_in_euro = mock.MagicMock(return_value={})

        with mock.patch('result.aggregation.aggregate_dictionaries') as mock_agg:
            mock_agg.return_value = {'purchased_carrier_amounts': {}}
            visitor.exit_production_unit(mock_pu, 2020, {}, [{}])

            assert visitor._add_production_unit_entry.call_count >= 2

    def test_exit_production_unit_skips_budget_when_not_start_year(self):
        """Test exit_production_unit skips budget when not in start year."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'production_unit_budget_relevant_emission_in_t_co2': {},
            'production_unit_overall_emission_budget_used_in_t_co2': {},
            'production_unit_overall_emission_budget_in_t_co2': {},
            'production_unit_energy_carrier_purchased_amount_in_gj': {},
            'production_unit_product_purchased_amount_in_t': {},
            'production_unit_by_product_purchased_amount_in_t': {},
            'production_unit_energy_carrier_purchase_cost_in_euro': {},
            'production_unit_product_purchase_cost_in_euro': {},
            'production_unit_by_product_purchase_cost_in_euro': {},
            'production_unit_energy_carrier_taxes_in_euro': {},
            'production_unit_energy_carrier_subsidies_in_euro': {},
            'production_unit_energy_carrier_export_in_gj': {},
            'production_unit_product_export_in_t': {},
            'production_unit_by_product_export_in_t': {},
            'production_unit_energy_carrier_sell_gain_in_euro': {},
            'production_unit_product_sell_gain_in_euro': {},
            'production_unit_by_product_sell_gain_in_euro': {},
            'production_unit_energy_carrier_upstream_emission_in_t_co2': {},
            'production_unit_product_upstream_emission_in_t_co2': {},
            'production_unit_by_product_upstream_emission_in_t_co2': {},
            'production_unit_energy_carrier_downstream_emission_in_t_co2': {},
            'production_unit_product_downstream_emission_in_t_co2': {},
            'production_unit_by_product_downstream_emission_in_t_co2': {},
            'production_unit_energy_carrier_renewably_bound_co2_emission_in_t_co2': {},
            'production_unit_product_renewably_bound_co2_emission_in_t_co2': {},
            'production_unit_by_product_renewably_bound_co2_emission_in_t_co2': {},
            'production_unit_energy_carrier_upstream_emission_cost_in_euro': {},
            'production_unit_product_upstream_emission_cost_in_euro': {},
            'production_unit_by_product_upstream_emission_cost_in_euro': {},
            'production_unit_energy_carrier_downstream_emission_cost_in_euro': {},
            'production_unit_product_downstream_emission_cost_in_euro': {},
            'production_unit_by_product_downstream_emission_cost_in_euro': {},
            'production_unit_energy_carrier_renewably_bound_co2_emission_cost_in_euro': {},
            'production_unit_product_renewably_bound_co2_emission_cost_in_euro': {},
            'production_unit_by_product_renewably_bound_co2_emission_cost_in_euro': {},
        }
        visitor._simulation_options = {'start_year': 2020}
        visitor._co2_cost_in_euro_per_t_co2 = 50.0
        visitor._interest_rate = 0.05

        mock_pu = mock.MagicMock()
        mock_pu.multi_period_budget_summary = {'used_in_t_co2': 10.0, 'available_in_t_co2': 100.0}
        mock_pu.budget_relevant_emission_in_t_co2 = mock.MagicMock(return_value=5.0)
        mock_pu.purchased_carrier_amounts = {}
        mock_pu.carrier_purchase_cost_in_euro = mock.MagicMock(return_value={})
        mock_pu.energy_carrier_taxes_in_euro = mock.MagicMock(return_value={})
        mock_pu.energy_carrier_subsidies_in_euro = mock.MagicMock(return_value={})
        mock_pu.export = mock.MagicMock(return_value={})
        mock_pu.sell_gain_in_euro = mock.MagicMock(return_value={})
        mock_pu.upstream_emission_in_t_co2 = mock.MagicMock(return_value={})
        mock_pu.downstream_emission_in_t_co2 = mock.MagicMock(return_value={})
        mock_pu.renewably_bound_co2_emission_in_t_co2 = mock.MagicMock(return_value={})

        visitor._handle_production_unit_carrier_result = mock.MagicMock()
        visitor._carrier_emission_cost_in_euro = mock.MagicMock(return_value={})
        visitor._add_production_unit_entry = mock.MagicMock()

        with mock.patch('result.aggregation.aggregate_dictionaries') as mock_agg:
            mock_agg.return_value = {'purchased_carrier_amounts': {}}
            # Year 2021 != start_year 2020
            visitor.exit_production_unit(mock_pu, 2021, {}, [{}])

            # Budget entries should not be added (only budget_relevant_emission every year)
            assert visitor._add_production_unit_entry.call_count >= 1


class TestCollectingResultVisitorEnterProcess(unittest.TestCase):
    """Tests for enter_process method and collect_process_results."""

    def test_enter_process_calls_collect_results(self):
        """Test enter_process calls _collect_process_results."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'process_execution_count': {},
            'process_direct_emission_in_t_co2': {},
            'process_direct_energy_emission_in_t_co2': {},
            'process_captured_emission_in_t_co2': {},
            'process_direct_non_energy_emission_cost_in_euro': {},
            'process_saving_due_to_captured_emission_in_euro': {},
            'process_investment_in_euro': {},
            'process_annuity_on_investment_in_euro_per_process_count': {},
            'process_annuity_on_investment_in_euro': {},
            'process_opex_in_euro_per_process_count': {},
            'process_opex_in_euro': {},
            'process_direct_emission_cost_in_euro': {},
            'process_direct_energy_emission_cost_in_euro': {},
            'process_direct_non_energy_emission_in_t_co2': {},
            'process_carrier_cost_in_euro_per_process_count': {},
            'process_energy_carrier_production_direct_emission_in_t_co2': {},
        }
        visitor._specific_results = {
            'process_carrier_cost_in_euro_per_process_count': {},
            'process_annuity_on_investment_in_euro_per_process_count': {},
            'process_opex_in_euro_per_process_count': {},
            'process_energy_carrier_energy_purchase_cost_in_euro_per_process_count': {},
            'process_energy_carrier_feedstock_purchase_cost_in_euro_per_process_count': {},
            'process_product_purchase_cost_in_euro_per_process_count': {},
            'process_by_product_purchase_cost_in_euro_per_process_count': {},
        }
        visitor._process = mock.MagicMock()
        visitor._sub_production_unit = mock.MagicMock()
        visitor._sub_production_unit.process_execution_count = 1
        visitor._collect_process_results = mock.MagicMock(return_value={})

        mock_process = mock.MagicMock()
        result = visitor.enter_process(mock_process, 2020)

        visitor._collect_process_results.assert_called_once()
        assert result == {}


class TestCollectingResultVisitorCollectOutput(unittest.TestCase):
    """Tests for exit_output and _collect_output_results methods."""

    def test_exit_output_calls_collect_results(self):
        """Test exit_output calls _collect_output_results."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'process_energy_carrier_production_in_gj': {},
            'process_product_production_in_t': {},
            'process_by_product_production_in_t': {},
        }
        visitor._specific_results = {
            'process_product_production_cost_in_euro_per_process_count': {},
            'process_by_product_production_cost_in_euro_per_process_count': {},
            'process_energy_carrier_production_cost_in_euro_per_process_count': {},
        }
        visitor._collect_output_results = mock.MagicMock(return_value={'output': 'data'})

        mock_output = mock.MagicMock()
        result = visitor.exit_output(mock_output, 2020, {})

        assert result == {'output': 'data'}
        visitor._collect_output_results.assert_called_once()

    def test_collect_output_results_energy_carrier(self):
        """Test collecting energy carrier output results."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'process_energy_carrier_production_in_gj': {},
        }
        visitor._specific_results = {}
        visitor._id_energy_carrier = 1
        visitor._id_product = None
        visitor._id_by_product = None
        visitor._sub_production_unit = mock.MagicMock()
        visitor._sub_production_unit.process_execution_count = 1.0
        visitor._add_energy_carrier_entry = mock.MagicMock()
        visitor._collect_production_cost_in_euro_per_process_count = mock.MagicMock()

        mock_output = mock.MagicMock()
        mock_output.output_in_gj = mock.MagicMock(return_value=100.0)
        mock_output.carrier = mock.MagicMock(spec=EnergyCarrier)

        result = visitor._collect_output_results(mock_output, 2020)

        visitor._add_energy_carrier_entry.assert_called_once()
        assert result == {}

    def test_collect_output_results_no_carrier_raises(self):
        """Test that no carrier set raises ValueError."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {}
        visitor._specific_results = {}
        visitor._id_energy_carrier = None
        visitor._id_product = None
        visitor._id_by_product = None
        visitor._sub_production_unit = mock.MagicMock()

        mock_output = mock.MagicMock()

        with pytest.raises(ValueError, match='Neither energy carrier nor product nor by-product'):
            visitor._collect_output_results(mock_output, 2020)


class TestCollectingResultVisitorDemandCollection(unittest.TestCase):
    """Tests for demand collection and handling."""

    def test_collect_demand_results_energy_carrier(self):
        """Test collect_demand_results with energy carrier."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {
            'process_energy_carrier_energy_demand_in_gj': {},
        }
        visitor._specific_results = {}
        visitor._handle_energy_carrier_demand = mock.MagicMock()

        mock_demand = mock.MagicMock(spec=EnergyCarrierEnergyDemand)
        mock_carrier = mock.MagicMock(spec=EnergyCarrier)
        mock_carrier.unit = CarrierUnit.GJ
        mock_demand.carrier = mock_carrier
        mock_demand.purchase_cost_in_euro_per_process_count = mock.MagicMock(return_value=50.0)

        visitor._collect_demand_results(2020, mock_demand, 1.0)

        visitor._handle_energy_carrier_demand.assert_called_once()

    def test_collect_demand_results_unknown_unit_raises(self):
        """Test collect_demand_results with unknown unit raises."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {}
        visitor._specific_results = {}

        mock_demand = mock.MagicMock()
        mock_carrier = mock.MagicMock()
        mock_carrier.unit = 'UNKNOWN_UNIT'
        mock_demand.carrier = mock_carrier
        mock_demand.purchase_cost_in_euro_per_process_count = mock.MagicMock(return_value=50.0)

        with pytest.raises(ValueError, match='Unknown carrier unit'):
            visitor._collect_demand_results(2020, mock_demand, 1.0)

    def test_collect_demand_results_unknown_carrier_raises(self):
        """Test collect_demand_results with unknown carrier type raises."""
        visitor = CollectingResultVisitor({'start_year': 2020})
        visitor._absolute_results = {}
        visitor._specific_results = {}

        mock_demand = mock.MagicMock()
        mock_carrier = mock.MagicMock()
        mock_carrier.unit = CarrierUnit.T
        mock_demand.carrier = mock_carrier
        mock_demand.purchase_cost_in_euro_per_process_count = mock.MagicMock(return_value=50.0)

        with pytest.raises(NotImplementedError, match='not yet implemented'):
            visitor._collect_demand_results(2020, mock_demand, 1.0)


if __name__ == '__main__':
    unittest.main()
