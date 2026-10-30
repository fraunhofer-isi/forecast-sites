# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import pytest
from test_utils.isi_mock import Mock, fixture, patch, patch_property

from carrier.carrier_unit import CarrierUnit
from optimization.optimization_result import OptimizationResult
from production_unit.production_unit import ProductionUnit

simulation_options = {
    'start_year': 2000,
    'interim_year': 2025,
    'end_year': 2050,
}


@fixture
def sut():
    site = Mock()
    sector = Mock()
    sub_production_unit_factory = Mock()
    sub_production_unit_factory.create_for_start_year = Mock([])

    production_unit = ProductionUnit(
        1,
        site,
        sector,
        {},
        sub_production_unit_factory,
        Mock(),
        {},
        [],
        simulation_options,
    )
    return production_unit


def test_construction(sut):
    assert sut is not None


def test_available_process_options(sut):
    process_option = Mock()
    sub_production_unit = Mock()
    sut._process_option_mapping = {process_option: sub_production_unit}
    result = sut.available_process_options
    assert result == [process_option]


def test_purchased_carrier_amounts(sut):
    sut.optimization_results = Mock(purchased_carrier_amounts='mocked_result')
    result = sut.purchased_carrier_amounts
    assert result == 'mocked_result'


def test_used_carriers(sut):
    sub_production_unit = Mock()
    sub_production_unit.used_carriers = ['mocked_carrier']
    sut.sub_production_units = [sub_production_unit]

    result = sut.used_carriers
    assert result == ['mocked_carrier']


def test_products(sut):
    sut._minimum_export_interpolation_data_in_t = {'mocked_product': 1}
    result = sut.products
    assert result == ['mocked_product']


def test_by_products(sut):
    sub_production_unit = Mock()
    sub_production_unit.output_by_products = ['mocked_by_product']
    sut.sub_production_units = [sub_production_unit]

    result = sut.by_products
    assert result == ['mocked_by_product']


def test_used_process_ids(sut):
    sub_production_unit = Mock()
    sub_production_unit.id_process = 1
    sut.sub_production_units = [sub_production_unit]

    result = sut.used_process_ids
    assert result == [1]


@patch(ProductionUnit._remove_inactive_sub_production_units)
@patch(ProductionUnit._process_option_to_sub_production_unit_mapping, {})
def test_optimize(sut):
    optimization = Mock()
    optimization.optimize = Mock(Mock(purchased_carrier_amounts={}, process_execution_counts={}))
    sut._optimization_factory.create = Mock(optimization)
    context = Mock()
    with patch(ProductionUnit._apply_results) as mocked_apply_results:
        sut.optimize(2020, context)
        assert sut._optimization_factory.create.called
        assert mocked_apply_results.called


class TestAccept:
    def test_with_no_sub_production_units(self, sut):
        visitor = Mock()
        visitor.exit_production_unit = Mock('mocked_result')
        sut.sub_production_units = []

        result = sut.accept(visitor, 2015)

        assert result == 'mocked_result'
        assert visitor.enter_production_unit.called
        assert visitor.exit_production_unit.called

    def test_normal_usage(self, sut):
        visitor = Mock()
        visitor.exit_production_unit = Mock('mocked_result')
        child = Mock()
        child.accept = Mock('child_result')
        sut.sub_production_units = [child]

        result = sut.accept(visitor, 2015)
        assert result == 'mocked_result'

        assert visitor.enter_production_unit.called
        assert child.accept.called
        assert visitor.exit_production_unit.called


def test_consume_purchased_carrier_amounts(sut):
    purchased_carrier_amounts = {
        'mocked_carrier': 0,
        'another_mocked_carrier': 100,
    }
    with (
        patch_property(ProductionUnit.purchased_carrier_amounts, purchased_carrier_amounts),
        patch(ProductionUnit._consume_purchased_carrier_amount) as mocked_consume,
    ):
        sut.consume_purchased_carrier_amounts(2020, Mock())
        assert mocked_consume.called


class TestExportProducedCarrierAmounts:
    """Tests for exporting produced carriers - no longer provides to pool."""
    @patch_property(ProductionUnit.used_carriers, ['mocked_carrier'])
    @patch(ProductionUnit._export_amount_for_carrier, 0)
    def test_with_zero_value(self, sut):
        # When export is zero, no carrier is exported
        sut.export_produced_carrier_amounts(2020)
        # No assertion on provide - that method was removed

    @patch_property(ProductionUnit.used_carriers, ['mocked_carrier'])
    @patch(ProductionUnit._export_amount_for_carrier, 10)
    def test_normal_usage(self, sut):
        # Export now just returns the export amounts, doesn't provide to pool
        # Method returns None - it just processes without returning value
        sut.export_produced_carrier_amounts(2020)


@patch_property(ProductionUnit.used_carriers, ['mocked_carrier'])
@patch(ProductionUnit._sell_gain_in_euro_for_carrier, 'mocked_sell_gain')
def test_sell_gain_in_euro(sut):
    result = sut.sell_gain_in_euro(2020)
    assert result['mocked_carrier'] == 'mocked_sell_gain'


@patch_property(ProductionUnit.used_carriers, ['mocked_carrier'])
@patch(ProductionUnit._export_amount_for_carrier, 'mocked_export')
def test_export(sut):
    result = sut.export(2020)
    assert result['mocked_carrier'] == 'mocked_export'


def test_new_investment_in_euro(sut):
    sub_production_unit = Mock()
    sub_production_unit.new_investment_in_euro = Mock(33)
    sut.sub_production_units = [sub_production_unit]
    result = sut.new_investment_in_euro(2015, 'mocked_simulation_options')
    assert result == 33


def test_carrier_purchase_cost_in_euro(sut):
    carrier = Mock()
    carrier.purchase_cost_in_euro = Mock('mocked_cost')
    purchased_carrier_amounts = {carrier: 3}
    with patch_property(ProductionUnit.purchased_carrier_amounts, purchased_carrier_amounts):
        result = sut.carrier_purchase_cost_in_euro(2015)
        assert result[carrier] == 'mocked_cost'


def test_energy_carrier_taxes_in_euro(sut):
    energy_carrier = Mock()
    energy_carrier.unit = CarrierUnit.GJ
    energy_carrier.taxes_in_euro_per_unit = Mock(5)
    product = Mock()
    product.unit = CarrierUnit.T
    purchased_carrier_amounts = {energy_carrier: 3, product: 7}
    with patch_property(ProductionUnit.purchased_carrier_amounts, purchased_carrier_amounts):
        result = sut.energy_carrier_taxes_in_euro(2020, {})
        assert result == {energy_carrier: 15}


def test_energy_carrier_subsidies_in_euro(sut):
    energy_carrier = Mock()
    energy_carrier.unit = CarrierUnit.GJ
    energy_carrier.subsidies_in_euro_per_unit = Mock(2)
    product = Mock()
    product.unit = CarrierUnit.T
    purchased_carrier_amounts = {energy_carrier: 3, product: 7}
    with patch_property(ProductionUnit.purchased_carrier_amounts, purchased_carrier_amounts):
        result = sut.energy_carrier_subsidies_in_euro(2020, {})
        assert result == {energy_carrier: 6}


def test_carrier_availability(sut):
    sut._site.carrier_availability = Mock('mocked_result')
    result = sut.carrier_availability('mocked_carrier', 2020)
    assert result == 'mocked_result'


class TestCarrierMinimumExportInT:
    def test_with_carrier(self, sut):
        interpolation_data = Mock()
        interpolation_data.value_for_start_year = 100
        sut._minimum_export_interpolation_data_in_t = {'mocked_carrier': interpolation_data}
        result = sut.carrier_minimum_export_in_t('mocked_carrier', 2000, simulation_options)

        assert result is not None

    def test_without_carrier(self, sut):
        interpolation_data = Mock()
        interpolation_data.value_for_start_year = 100
        sut._minimum_export_interpolation_data_in_t = {'mocked_carrier': interpolation_data}
        result = sut.carrier_minimum_export_in_t('another_carrier', 2000, simulation_options)
        assert result == 0


def test_upstream_emission_in_t_co2(sut):
    carrier = Mock()
    carrier.upstream_emission_in_t_co2_per_unit = Mock(5)
    purchased_carrier_amounts = {carrier: 3}
    with patch_property(ProductionUnit.purchased_carrier_amounts, purchased_carrier_amounts):
        result = sut.upstream_emission_in_t_co2(2020, 'mocked_simulation_options')
        assert result[carrier] == 15


def test_number_of_process_usages(sut):
    process = Mock()
    sub_production_unit = Mock()
    sub_production_unit.number_of_process_usages = Mock(33)
    sut.sub_production_units = [sub_production_unit]
    result = sut.number_of_process_usages(process)
    assert result == 33


@patch(ProductionUnit._export_amount_for_carrier, 10)
def test_sell_gain_in_euro_for_carrier(sut):
    carrier = Mock()
    carrier.sell_price_in_euro_per_unit = Mock(3)
    result = sut._sell_gain_in_euro_for_carrier(2020, carrier)
    assert result == 30


@patch(
    ProductionUnit._netto_produced_or_consumed_amount_for_carrier_from_sub_production_units,
    10,
)
class TestExportAmountForCarrier:
    @patch_property(ProductionUnit.purchased_carrier_amounts, {'mocked_carrier': 5})
    def test_normal_usage(self, sut):
        result = sut._export_amount_for_carrier(2020, 'mocked_carrier')
        assert result == 15

    @patch_property(ProductionUnit.purchased_carrier_amounts, {'mocked_carrier': -15})
    def test_large_negative_value(self, sut):
        with pytest.raises(ValueError, match='must not be negative'):
            sut._export_amount_for_carrier(2020, 'mocked_carrier')

    @patch_property(ProductionUnit.purchased_carrier_amounts, {'mocked_carrier': -10 - 1e-10})
    def test_small_negative_value(self, sut):
        result = sut._export_amount_for_carrier(2020, 'mocked_carrier')
        assert result == 0


@patch(ProductionUnit._extract_process_execution_counts_for_start_year)
@patch(ProductionUnit._determine_purchased_carrier_amounts_for_start_year)
@patch(OptimizationResult.__init__, None)
def test_extract_pseudo_optimization_results_for_start_year(sut):
    result = sut._extract_pseudo_optimization_results_for_start_year(simulation_options)
    assert isinstance(result, OptimizationResult)


class TestDeterminePurchasedCarrierAmountsForStartYear:
    def test_normal_usage(self, sut):
        energy_carrier = Mock(unit=CarrierUnit.GJ)
        product = Mock(unit=CarrierUnit.T)
        by_product = Mock(unit=CarrierUnit.T)

        sut.available_carriers = [energy_carrier, product, by_product]
        interpolation_data = Mock()
        interpolation_data.value_for_start_year = 30
        sut._minimum_export_interpolation_data_in_t = {product: interpolation_data}

        sub_production_unit = Mock()

        def netto_side_effect(_year, carrier):
            if carrier == energy_carrier:
                return -70  # consumption increases purchase need
            if carrier == product:
                return 10  # production reduces purchase need
            if carrier == by_product:
                return 0
            return 0

        sub_production_unit.netto_produced_or_consumed_amount_for_carrier = Mock(side_effect=netto_side_effect)
        sut.sub_production_units = [sub_production_unit]

        result = sut._determine_purchased_carrier_amounts_for_start_year(simulation_options)
        assert result[energy_carrier] == 70  # 0 - (-70)
        assert result[product] == 20  # 30 - 10
        assert result[by_product] == 0

    def test_negative_after_subtraction_clamped_to_zero(self, sut):
        product = Mock(unit=CarrierUnit.T)
        sut.available_carriers = [product]
        interpolation_data = Mock()
        interpolation_data.value_for_start_year = 10
        sut._minimum_export_interpolation_data_in_t = {product: interpolation_data}
        sub_unit = Mock()
        sub_unit.netto_produced_or_consumed_amount_for_carrier = Mock(return_value=50)  # export > requirement
        sut.sub_production_units = [sub_unit]
        result = sut._determine_purchased_carrier_amounts_for_start_year(simulation_options)
        assert result[product] == 0


def test_netto_produced_or_consumed_amount_for_carrier_from_sub_production_units(sut):
    carrier = Mock()
    sub_one = Mock()
    sub_one.netto_produced_or_consumed_amount_for_carrier = Mock(return_value=10)
    sub_two = Mock()
    sub_two.netto_produced_or_consumed_amount_for_carrier = Mock(return_value=-3)
    sut.sub_production_units = [sub_one, sub_two]
    year = simulation_options['start_year']
    result = sut._netto_produced_or_consumed_amount_for_carrier_from_sub_production_units(year, carrier)
    assert result == 7


@patch_property(ProductionUnit.available_process_options, ['mocked_process_option'])
@patch(
    ProductionUnit._extract_process_execution_counts_from_existing_sub_production_units,
    'mocked_result',
)
def test_extract_process_execution_counts_for_start_year(sut):
    result = sut._extract_process_execution_counts_for_start_year()
    assert result == 'mocked_result'


def test_extract_process_execution_counts_from_existing_sub_production_units(sut):
    sub_production_unit = Mock()
    sub_production_unit.process_execution_count = 8
    sut.sub_production_units = [sub_production_unit]
    mocked_reverse_mapping = {sub_production_unit: 'mocked_process_option'}

    with patch_property(ProductionUnit._reverse_process_option_mapping, mocked_reverse_mapping):
        process_execution_counts = {'another_mocked_process_option': 0}
        result = sut._extract_process_execution_counts_from_existing_sub_production_units(process_execution_counts)
        assert result['mocked_process_option'] == 8


def test_initialize_sub_production_inactivity(sut):
    sub_zero = Mock(process_execution_count=0)
    sub_non_zero = Mock(process_execution_count=5)
    sut.sub_production_units = [sub_zero, sub_non_zero]
    result = sut._initialize_sub_production_inactivity()
    assert result[sub_zero] == 1
    assert result[sub_non_zero] == 0


def test_remove_inactive_sub_production_units(sut):
    mocked_sub_production_unit = Mock()

    sut._sub_production_unit_inactivity = {mocked_sub_production_unit: 5}

    sut.sub_production_units = [mocked_sub_production_unit]
    mocked_sub_production_unit.year_of_last_reinvestment = 2020
    sut._remove_inactive_sub_production_units(2020)

    assert sut.sub_production_units == []


def test_remove_inactive_sub_production_units_keeps_future_planned_spu(sut):
    mocked_sub_production_unit = Mock(year_of_last_reinvestment=2030)
    sut._sub_production_unit_inactivity = {mocked_sub_production_unit: 5}
    sut.sub_production_units = [mocked_sub_production_unit]

    sut._remove_inactive_sub_production_units(2020)

    assert sut.sub_production_units == [mocked_sub_production_unit]
    assert sut._sub_production_unit_inactivity[mocked_sub_production_unit] == 5


def test_process_option_to_sub_production_unit_mapping(sut):
    # one original processes and one installed processes
    process = Mock()
    sut._original_processes = [process]
    installed_sub = Mock()
    installed_sub.installed_process = Mock()
    installed_sub.process_execution_count = 0
    sut.sub_production_units = [installed_sub]
    mapping = sut._process_option_to_sub_production_unit_mapping()
    assert len(mapping) == 2
    assert any(v is None for v in mapping.values())
    assert any(v is not None for v in mapping.values())


@patch(ProductionUnit._create_or_update_sub_production_units)
@patch(ProductionUnit.consume_purchased_carrier_amounts)
@patch(ProductionUnit.export_produced_carrier_amounts)
def test_apply_results(sut):
    sut.optimization_results = Mock()
    sut._apply_results(2022, Mock())
    assert ProductionUnit._create_or_update_sub_production_units.called
    assert ProductionUnit.consume_purchased_carrier_amounts.called
    assert ProductionUnit.export_produced_carrier_amounts.called


def test_consume_purchased_carrier_amount(sut):
    sut._site.consume_purchased_carrier_amount = Mock()
    sut._consume_purchased_carrier_amount(
        'mocked_carrier',
        10,
        2020,
        'mocked_context',
    )
    assert sut._site.consume_purchased_carrier_amount.called


# test_provide_produced_carrier_amount - removed method, test deleted


class TestCreateOrUpdateSubProductionUnits:
    def test_with_no_existing_sub_production_unit(self, sut):
        sut._process_option_mapping = {'mocked_process_option': None}
        sut.optimization_results.process_execution_counts = {'mocked_process_option': 5}
        sut._sub_production_unit_factory.create_sub_production_unit_for_process_option = Mock()

        sut._create_or_update_sub_production_units(2020)

        assert sut._sub_production_unit_factory.create_sub_production_unit_for_process_option.called

    class TestWithExistingSubProductionUnit:
        def test_with_used_sub_production_unit(self, sut):
            sub_production_unit = Mock()
            sut._process_option_mapping = {'mocked_process_option': sub_production_unit}
            sut.optimization_results.process_execution_counts = {'mocked_process_option': 5}
            sut._sub_production_unit_inactivity = {sub_production_unit: 3}

            sut._create_or_update_sub_production_units(2020)

            assert sub_production_unit.process_execution_count == 5
            assert sut._sub_production_unit_inactivity[sub_production_unit] == 0

        def test_with_unused_sub_production_unit(self, sut):
            sub_production_unit = Mock(year_of_last_reinvestment=2020)
            sut._process_option_mapping = {'mocked_process_option': sub_production_unit}
            sut.optimization_results.process_execution_counts = {'mocked_process_option': 0}
            sut._sub_production_unit_inactivity = {sub_production_unit: 0}

            sut._create_or_update_sub_production_units(2020)

            assert sub_production_unit.process_execution_count == 0
            assert sut._sub_production_unit_inactivity[sub_production_unit] == 1

        def test_with_unused_future_planned_sub_production_unit(self, sut):
            sub_production_unit = Mock(year_of_last_reinvestment=2025)
            sut._process_option_mapping = {'mocked_process_option': sub_production_unit}
            sut.optimization_results.process_execution_counts = {'mocked_process_option': 0}
            sut._sub_production_unit_inactivity = {sub_production_unit: 0}

            sut._create_or_update_sub_production_units(2020)

            assert sub_production_unit.process_execution_count == 0
            assert sut._sub_production_unit_inactivity[sub_production_unit] == 0


class TestDownstreamEmission:
    """Test downstream emission calculations."""

    def test_downstream_emission_no_carriers(self, sut):
        """Test downstream emission with no export."""
        sut.export = Mock(return_value={})

        result = sut.downstream_emission_in_t_co2(2020, {})

        assert result == {}

    def test_downstream_emission_carrier_without_attribute(self, sut):
        """Test downstream emission when carrier lacks attribute."""
        carrier = Mock(spec=[])  # No downstream_emission_in_t_co2_per_unit
        sut.export = Mock(return_value={carrier: 10.0})

        result = sut.downstream_emission_in_t_co2(2020, {})

        assert carrier not in result

    def test_downstream_emission_zero_export(self, sut):
        """Test downstream emission with zero export."""
        carrier = Mock()
        carrier.downstream_emission_in_t_co2_per_unit = Mock(return_value=5.0)
        sut.export = Mock(return_value={carrier: 0.0})

        result = sut.downstream_emission_in_t_co2(2020, {})

        assert carrier not in result

    def test_downstream_emission_with_negative_export_in_epsilon(self, sut):
        """Test downstream emission with small negative export (numerical precision)."""
        carrier = Mock()
        carrier.downstream_emission_in_t_co2_per_unit = Mock(return_value=5.0)
        sut.export = Mock(return_value={carrier: -0.0001})  # Within epsilon

        result = sut.downstream_emission_in_t_co2(2020, {})

        # Should treat as 0 and not include
        assert carrier not in result

    def test_downstream_emission_with_large_negative_export_raises(self, sut):
        """Test downstream emission with significant negative export raises error."""
        carrier = Mock()
        sut.export = Mock(return_value={carrier: -1.0})  # Beyond epsilon

        with pytest.raises(ValueError, match='must not be negative'):
            sut.downstream_emission_in_t_co2(2020, {})

    def test_downstream_emission_with_valid_export(self, sut):
        """Test downstream emission with valid export."""
        carrier = Mock()
        carrier.downstream_emission_in_t_co2_per_unit = Mock(return_value=5.0)
        sut.export = Mock(return_value={carrier: 10.0})

        result = sut.downstream_emission_in_t_co2(2020, {})

        assert result[carrier] == 50.0


class TestBudgetRelevantEmission:
    """Test budget-relevant emission calculations with scope."""

    def test_budget_relevant_emission_direct_only(self, sut):
        """Test emission with direct scope only."""
        sub_pu = Mock()
        sub_pu.direct_emissions_in_t_co2 = Mock(return_value=100.0)
        sub_pu.installed_process.emission.captured_emission_in_t_co2 = Mock(return_value=10.0)

        sut.sub_production_units = [sub_pu]
        sut.upstream_emission_in_t_co2 = Mock(return_value={})
        sut.renewably_bound_co2_emission_in_t_co2 = Mock(return_value={})
        sut.downstream_emission_in_t_co2 = Mock(return_value={})

        simulation_options = {'emission_constraint_scope': frozenset({'direct'})}
        result = sut.budget_relevant_emission_in_t_co2(2020, simulation_options)

        assert result == 90.0  # 100 - 10

    def test_budget_relevant_emission_all_scopes(self, sut):
        """Test emission with all scopes included."""
        sub_pu = Mock()
        sub_pu.direct_emissions_in_t_co2 = Mock(return_value=100.0)
        sub_pu.installed_process.emission.captured_emission_in_t_co2 = Mock(return_value=10.0)

        sut.sub_production_units = [sub_pu]
        sut.upstream_emission_in_t_co2 = Mock(return_value={Mock(): 20.0})
        sut.renewably_bound_co2_emission_in_t_co2 = Mock(return_value={Mock(): 5.0})
        sut.downstream_emission_in_t_co2 = Mock(return_value={Mock(): 15.0})

        simulation_options = {'emission_constraint_scope': frozenset({'direct', 'upstream', 'renewably_bound', 'downstream'})}
        result = sut.budget_relevant_emission_in_t_co2(2020, simulation_options)

        # (100 - 10) + 20 - 5 + 15 = 120
        assert result == 120.0

    def test_budget_relevant_emission_upstream_only(self, sut):
        """Test emission with upstream scope only."""
        sut.sub_production_units = []
        sut.upstream_emission_in_t_co2 = Mock(return_value={Mock(): 30.0})
        sut.renewably_bound_co2_emission_in_t_co2 = Mock(return_value={})
        sut.downstream_emission_in_t_co2 = Mock(return_value={})

        simulation_options = {'emission_constraint_scope': frozenset({'upstream'})}
        result = sut.budget_relevant_emission_in_t_co2(2020, simulation_options)

        assert result == 30.0

    def test_budget_relevant_emission_renewably_bound_only(self, sut):
        """Test emission with renewably bound scope only."""
        sut.sub_production_units = []
        sut.upstream_emission_in_t_co2 = Mock(return_value={})
        sut.renewably_bound_co2_emission_in_t_co2 = Mock(return_value={Mock(): 25.0})
        sut.downstream_emission_in_t_co2 = Mock(return_value={})

        simulation_options = {'emission_constraint_scope': frozenset({'renewably_bound'})}
        result = sut.budget_relevant_emission_in_t_co2(2020, simulation_options)

        assert result == -25.0  # Subtracted


class TestMultiPeriodBudgetSummary:
    """Test multi-period budget summary property."""

    def test_multi_period_budget_summary_none_result(self, sut):
        """Test budget summary when no multi-period result."""
        sut._multi_period_result = None

        result = sut.multi_period_budget_summary

        assert result is None

    def test_multi_period_budget_summary_with_result(self, sut):
        """Test budget summary with multi-period result."""
        mock_summary = Mock()
        mock_result = Mock()
        mock_result.overall_emission_budget_summary = mock_summary
        sut._multi_period_result = mock_result

        result = sut.multi_period_budget_summary

        assert result is mock_summary


class TestFindSubProductionUnit:
    """Tests for _find_sub_production_unit_for_installed_process helper method."""

    def test_returns_sub_unit_when_installed_process_matches(self, sut):
        """When installed process matches, return the corresponding sub_production_unit."""
        # Create installed process objects (use same object reference for identity comparison)
        installed_process_1 = Mock()
        installed_process_2 = Mock()
        installed_process_3 = Mock()

        sub_unit_1 = Mock(installed_process=installed_process_1)
        sub_unit_2 = Mock(installed_process=installed_process_2)
        sub_unit_3 = Mock(installed_process=installed_process_3)

        sut.sub_production_units = [sub_unit_1, sub_unit_2, sub_unit_3]

        # Search for installed_process_2 (use same object reference)
        result = sut._find_sub_production_unit_for_installed_process(installed_process_2)

        # Verify we got the right sub_unit back
        assert result == sub_unit_2

    def test_returns_none_when_no_match(self, sut):
        """When no sub_production_unit has the installed process, return None."""
        installed_process_1 = Mock()
        installed_process_2 = Mock()
        installed_process_search = Mock()  # Not in list

        sub_unit_1 = Mock(installed_process=installed_process_1)
        sub_unit_2 = Mock(installed_process=installed_process_2)

        sut.sub_production_units = [sub_unit_1, sub_unit_2]

        result = sut._find_sub_production_unit_for_installed_process(installed_process_search)

        assert result is None

    def test_returns_first_match_when_multiple(self, sut):
        """When process matches multiple units, return the first one (should not happen in practice)."""
        installed_process = Mock()

        sub_unit_1 = Mock(installed_process=installed_process)
        sub_unit_2 = Mock(installed_process=installed_process)  # Same process object

        sut.sub_production_units = [sub_unit_1, sub_unit_2]

        result = sut._find_sub_production_unit_for_installed_process(installed_process)

        # Should return the first matching unit
        assert result == sub_unit_1

    def test_returns_none_when_empty_list(self, sut):
        """When there are no sub_production_units, return None."""
        sut.sub_production_units = []

        result = sut._find_sub_production_unit_for_installed_process(Mock())

        assert result is None


class TestApplyMultiPeriodResults:
    """Tests for _apply_multi_period_results method."""

    def test_apply_multi_period_results_calls_helper_methods(self, sut):
        """Test that _apply_multi_period_results calls create_or_update and carrier handling methods."""
        sut._create_or_update_sub_production_units_from_multi_period = Mock()
        sut.consume_purchased_carrier_amounts = Mock()
        sut.export_produced_carrier_amounts = Mock()
        context = Mock()

        sut._apply_multi_period_results(2025, context)

        sut._create_or_update_sub_production_units_from_multi_period.assert_called_once_with(2025)
        sut.consume_purchased_carrier_amounts.assert_called_once_with(2025, context)
        sut.export_produced_carrier_amounts.assert_called_once_with(2025)


class TestCreateOrUpdateSubProductionUnitsFromMultiPeriod:
    """Tests for _create_or_update_sub_production_units_from_multi_period method."""

    def test_raises_when_multi_period_result_not_cached(self, sut):
        """Test that method raises RuntimeError if _multi_period_result is None."""
        sut._multi_period_result = None
        sut.optimization_results = Mock(process_execution_counts={})

        with pytest.raises(RuntimeError, match='Expected cached multi-period result'):
            sut._create_or_update_sub_production_units_from_multi_period(2025)


class TestCreateOrUpdateSubProductionUnitsBranches:
    """Tests for _create_or_update_sub_production_units method - specific branches."""

    def test_create_new_unit_when_process_not_used(self, sut):
        """Test the 501->497 branch: when process_is_used is False for new unit."""
        process_option = Mock()
        sut._process_option_mapping = {process_option: None}  # No unit yet
        sut._sub_production_unit_factory = Mock()
        sut.sub_production_units = []
        sut._sub_production_unit_inactivity = {}
        sut.optimization_results = Mock(
            process_execution_counts={process_option: 0}  # Not used
        )

        sut._create_or_update_sub_production_units(2025)

        # Factory should NOT be called since process not used
        sut._sub_production_unit_factory.create_sub_production_unit_for_process_option.assert_not_called()


class TestSplitExecutionAcrossVintages:
    """Tests for _split_execution_across_vintages method."""

    def test_split_with_zero_total_capacity(self, sut):
        """Test splitting when total capacity is zero."""
        vintage1 = Mock(max_process_execution_count=0, process_execution_count=None)
        vintage2 = Mock(max_process_execution_count=0, process_execution_count=None)
        vintages = [vintage1, vintage2]
        sut._sub_production_unit_inactivity = {}
        sut._is_future_planned_sub_production_unit = Mock(return_value=False)

        sut._split_execution_across_vintages(vintages, 100, 2025)

        # Both should be set to 0
        assert vintage1.process_execution_count == 0
        assert vintage2.process_execution_count == 0

    def test_split_with_positive_total_capacity(self, sut):
        """Test splitting when total capacity > 0."""
        vintage1 = Mock(max_process_execution_count=50)
        vintage2 = Mock(max_process_execution_count=50)
        vintages = [vintage1, vintage2]
        sut._sub_production_unit_inactivity = {vintage1: 0, vintage2: 0}
        sut._is_future_planned_sub_production_unit = Mock(return_value=False)

        sut._split_execution_across_vintages(vintages, 100, 2025)

        # Total should be distributed (vintage1 gets 50, vintage2 gets remaining 50)
        assert vintage1.process_execution_count == 50
        assert vintage2.process_execution_count == 50

    def test_split_with_unequal_capacity(self, sut):
        """Test splitting with unequal vintage capacities."""
        vintage1 = Mock(max_process_execution_count=30)
        vintage2 = Mock(max_process_execution_count=70)
        vintages = [vintage1, vintage2]
        sut._sub_production_unit_inactivity = {vintage1: 0, vintage2: 0}
        sut._is_future_planned_sub_production_unit = Mock(return_value=False)

        sut._split_execution_across_vintages(vintages, 100, 2025)

        # vintage1 should get 30 (30% of 100)
        assert vintage1.process_execution_count == 30
        # vintage2 should get remaining (70)
        assert vintage2.process_execution_count == 70

    def test_split_with_zero_execution_count_and_future_planned(self, sut):
        """Test line 615-616: when execution_count is 0 but unit is future planned."""
        vintage1 = Mock(max_process_execution_count=50)
        vintages = [vintage1]
        sut._sub_production_unit_inactivity = {vintage1: 2}
        sut._is_future_planned_sub_production_unit = Mock(return_value=True)

        sut._split_execution_across_vintages(vintages, 0, 2025)

        # Should set to 0
        assert vintage1.process_execution_count == 0
        # Since it's future planned, inactivity shouldn't increment
        assert sut._sub_production_unit_inactivity[vintage1] == 2
