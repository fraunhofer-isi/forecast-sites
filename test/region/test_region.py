# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import logging

import pandas as pd
import pytest
from test_utils.isi_mock import Mock, fixture, patch

from carrier.carrier_unit import CarrierUnit
from optimization.optimization_type import OptimizationType
from region.region import Region


@fixture
@patch(Region._initialize_carrier_availability)
def sut():
    id_region = 1
    energy_carrier_map = Mock()
    sector_map = Mock()
    product_map = Mock()
    by_product_map = Mock()

    site_factory = Mock()

    region = Region(
        id_region,
        'mocked_data_interface',
        energy_carrier_map,
        sector_map,
        product_map,
        by_product_map,
        'mocked_process_map',
        site_factory,
        'mocked_simulation_options',
    )
    return region


def test_construction(sut):
    assert sut is not None


def test_id_scenario(sut):
    sut._data_interface = Mock()
    sut._data_interface.id_scenario = 'mocked_id_scenario'

    result = sut.id_scenario
    assert result == 'mocked_id_scenario'


def test_interest_rate(sut):
    sut._data_interface = Mock()
    sut._data_interface.interest_rate = 0.07
    result = sut.interest_rate
    assert result == 0.07


def test_site_data(sut):
    sut._data_interface = Mock()
    sut._data_interface.site_data = 'mocked_site_data'
    result = sut.site_data
    assert result == 'mocked_site_data'


def test_sectors(sut):
    mocked_site1 = Mock()
    mocked_site1.sectors = ['sector1', 'sector2']
    mocked_site2 = Mock()
    mocked_site2.sectors = ['sector2', 'sector3']
    sut.sites = [mocked_site1, mocked_site2]

    result = sut.sectors
    assert result == {'sector1', 'sector2', 'sector3'}


def test_simulation_options_property(sut):
    sut._simulation_options = {'start_year': 2020}

    assert sut.simulation_options == {'start_year': 2020}


def test_data_interface_property(sut):
    sut._data_interface = 'mocked_data_interface'

    assert sut.data_interface == 'mocked_data_interface'


def test_energy_carrier_map_property(sut):
    sut._energy_carrier_map = {'power': 'carrier'}

    assert sut.energy_carrier_map == {'power': 'carrier'}


def test_product_map_property(sut):
    sut._product_map = {'steel': 'product'}

    assert sut.product_map == {'steel': 'product'}


def test_by_product_map_property(sut):
    sut._by_product_map = {'slag': 'by-product'}

    assert sut.by_product_map == {'slag': 'by-product'}


class TestDefaultCarrierAvailability:
    def test_carrier_unit_t(self, sut):
        carrier = Mock(unit=CarrierUnit.T)
        result = sut._default_carrier_availability(carrier)
        assert result == 0

    def test_carrier_unit_gj(self, sut):
        carrier = Mock(unit=CarrierUnit.GJ)
        result = sut._default_carrier_availability(carrier)
        assert result == 10e10

    def test_carrier_unit_unknown(self, sut):
        carrier = Mock(unit='unknown')
        with pytest.raises(TypeError, match='Unknown unit'):
            sut._default_carrier_availability(carrier)


def test_accept(sut):
    mocked_site = Mock()
    sut.sites = [mocked_site]
    visitor = Mock()
    sut.accept(visitor, 2020)
    assert visitor.enter_region.called
    assert mocked_site.accept.called
    assert visitor.exit_region.called


def test_consume_purchased_carrier_amounts_for_start_year(sut):
    mocked_site = Mock()
    sut.sites = [mocked_site]
    sut.consume_purchased_carrier_amounts_for_start_year(2020)
    assert mocked_site.consume_purchased_carrier_amounts_for_start_year.called


class TestConsumePurchasedCarrierAmount:
    def test_with_negative_value(self, sut):
        with pytest.raises(ValueError, match='Purchased carrier amount never must be < 0'):
            sut.consume_purchased_carrier_amount(
                'mocked_carrier',
                -10,
                2020,
                'mocked_context',
            )

    def test_without_entry(self, sut):
        sut._carrier_availability = {}

        with pytest.raises(KeyError):
            sut.consume_purchased_carrier_amount(
                'mocked_carrier',
                10,
                2020,
                'mocked_context',
            )

    def test_with_negative_availability(self, sut):
        mocked_series = pd.Series({'2020': -10, '2021': -20})
        sut._carrier_availability = {'mocked_carrier': mocked_series}
        context = Mock()
        context.simulation_options = {'start_year': 2020}

        with patch(logging.error) as mocked_logging_error:
            sut.consume_purchased_carrier_amount(
                'mocked_carrier',
                10,
                2020,
                context,
            )
            assert mocked_logging_error.called
            assert sut._carrier_availability['mocked_carrier']['2020'] == -20

    def test_with_available_amount(self, sut):
        mocked_series = pd.Series({'2020': 11, '2021': 12})
        sut._carrier_availability = {'mocked_carrier': mocked_series}

        sut.consume_purchased_carrier_amount(
            'mocked_carrier',
            10,
            2020,
            'mocked_context',
        )

        assert sut._carrier_availability['mocked_carrier']['2020'] == 1

    def test_with_larger_amount_in_start_year(self, sut):
        mocked_series = pd.Series({'2020': 10, '2021': 20})
        sut._carrier_availability = {'mocked_carrier': mocked_series}
        context = Mock()
        context.simulation_options = {'start_year': 2020}

        with patch(logging.error) as mocked_logging_error:
            sut.consume_purchased_carrier_amount(
                'mocked_carrier',
                100,
                2020,
                context,
            )
            assert mocked_logging_error.called
            assert sut._carrier_availability['mocked_carrier']['2020'] == -90

    def test_with_larger_amount_after_start_year(self, sut):
        mocked_series = pd.Series({'2020': 10, '2021': 20})
        sut._carrier_availability = {'mocked_carrier': mocked_series}
        context = Mock()
        context.simulation_options = {'start_year': 2010}

        with pytest.raises(ValueError, match='not available in sufficient amount'):
            sut.consume_purchased_carrier_amount(
                'mocked_carrier',
                100,
                2020,
                context,
            )


# provide_produced_carrier_amounts_for_start_year removed - test deleted
# TestProvideProducedCarrierAmount removed - method deleted


def test_co2_cost_in_euro_per_t_co2(sut):
    sut._data_interface = Mock()
    sut._data_interface.co2_cost_in_euro_per_t_co2 = Mock('mocked_co2_cost')
    result = sut.co2_cost_in_euro_per_t_co2(2020)
    assert result == 'mocked_co2_cost'


class TestCarrierAvailability:
    def test_without_entry(self, sut):
        sut._carrier_availability = {}
        mocked_series = pd.Series({'2020': 11, '2021': 12})
        sut._default_carrier_availability_series = Mock(mocked_series)

        result = sut.carrier_availability('mocked_carrier', 2020)
        assert result == 11

    def test_with_entry(self, sut):
        mocked_series = pd.Series({'2020': 11, '2021': 12})
        sut._carrier_availability = {'mocked_carrier': mocked_series}

        result = sut.carrier_availability('mocked_carrier', 2020)
        assert result == 11


class TestProcessIdsForSite:
    def test_with_site(self, sut):
        mocked_site = Mock()
        mocked_site.used_process_ids = 'mocked_result'
        sut._site = Mock(mocked_site)

        result = sut.process_ids_for_site(2)

        assert result == 'mocked_result'

    def test_without_site(self, sut):
        sut._site = Mock(None)

        result = sut.process_ids_for_site(2)

        assert result == []


def test_site(sut):
    mocked_site = Mock()
    sut.sites = [mocked_site]
    result = sut._site(10)
    assert result is None


def test_default_carrier_availability_series(sut):
    sut._default_carrier_availability = Mock(10)
    sut._data_interface = Mock()
    sut._data_interface.annual_value_series = Mock('mocked_result')
    result = sut._default_carrier_availability_series('mocked_carrier', 2020)
    assert result == 'mocked_result'


def test_initialize_carrier_availability(sut):
    sut._include_energy_carrier_availability = Mock('mocked_include_energy')
    sut._include_product_availability = Mock('mocked_include_product')
    sut._include_by_product_availability = Mock('mocked_include_by_product')

    sut._initialize_carrier_availability()

    assert sut._include_energy_carrier_availability.called
    assert sut._include_product_availability.called
    assert sut._include_by_product_availability.called


def test_optimize_collects_all_production_units(monkeypatch, sut):
    class _ProductionUnit:
        def _remove_inactive_sub_production_units(self, year):
            self.removed = year

        def _process_option_to_sub_production_unit_mapping(self):
            return {}

    pu1 = _ProductionUnit()
    pu2 = _ProductionUnit()
    sut.sites = [Mock(production_units=[pu1]), Mock(production_units=[pu2])]

    calls = {'optimized': False, 'applied': False}

    class FakeOptimization:
        def __init__(self, year, region, production_units, context):
            assert production_units == [pu1, pu2]

        def optimize(self):
            calls['optimized'] = True
            return 'region-result'

    class FakeApplier:
        def apply_for_year(self, year, region_result, production_units, context):
            calls['applied'] = True

    monkeypatch.setattr('region.region.RegionMultiPeriodOptimization', FakeOptimization)
    monkeypatch.setattr('region.region.RegionResultApplier', FakeApplier)

    context = Mock()
    context.simulation_options = {'optimization_type': OptimizationType.REGION_MULTI_PERIOD}
    sut.optimize(2030, context)

    assert calls == {'optimized': True, 'applied': True}


class TestIncludeEnergyCarrierAvailability:
    def test_without_entries(self, sut):
        sut._energy_carrier_map = {1: 'mocked_energy_carrier'}
        sut._data_interface = Mock()
        sut._data_interface.energy_carrier_availability_series = Mock(None)
        result = sut._include_energy_carrier_availability({})
        assert result == {}

    def test_with_entries(self, sut):
        sut._energy_carrier_map = {1: 'mocked_energy_carrier'}
        sut._data_interface = Mock()
        sut._data_interface.energy_carrier_availability_series = Mock(pd.Series({'2020': 11, '2021': 12}))
        result = sut._initialize_carrier_availability()
        energy_carrier_series = result['mocked_energy_carrier']
        assert energy_carrier_series['2020'] == 11
        assert energy_carrier_series['2021'] == 12


class TestIncludeProductAvailability:
    def test_without_entries(self, sut):
        sut._product_map = {1: 'mocked_product'}
        sut._data_interface = Mock()
        sut._data_interface.product_availability_series = Mock(None)

        result = sut._include_product_availability({})
        assert result == {}

    def test_with_entries(self, sut):
        sut._product_map = {1: 'mocked_product'}
        sut._data_interface = Mock()
        sut._data_interface.product_availability_series = Mock(pd.Series({'2020': 13, '2021': 14}))

        result = sut._initialize_carrier_availability()
        product_series = result['mocked_product']
        assert product_series['2020'] == 13
        assert product_series['2021'] == 14


class TestIncludeByProductAvailability:
    def test_without_entries(self, sut):
        sut._by_product_map = {1: 'mocked_by_product'}
        sut._data_interface = Mock()
        sut._data_interface.by_product_availability_series = Mock(None)

        result = sut._include_by_product_availability({})
        assert result == {}

    def test_with_entries(self, sut):
        sut._by_product_map = {1: 'mocked_by_product'}
        sut._data_interface = Mock()
        sut._data_interface.by_product_availability_series = Mock(pd.Series({'2020': 13, '2021': 14}))

        result = sut._initialize_carrier_availability()
        by_product_series = result['mocked_by_product']
        assert by_product_series['2020'] == 13
        assert by_product_series['2021'] == 14


def test_optimize_with_multi_period_cached_result(monkeypatch, sut):
    """Test optimize skips optimization when multi-period result is cached for year."""
    from optimization.region_multi_period_optimization_result import (
        RegionMultiPeriodOptimizationResult,
    )

    # Setup cached result
    mock_cached_result = Mock(spec=RegionMultiPeriodOptimizationResult)
    mock_cached_result.has_result_for_year.return_value = True
    sut._cached_multi_period_result = mock_cached_result
    sut._cached_production_units = []
    sut.sites = []

    # Verify optimization is skipped
    calls = {'optimization_called': False}

    class TrackingOptimization:
        def __init__(self, *args, **kwargs):
            calls['optimization_called'] = True

        def optimize(self):
            return None

    monkeypatch.setattr('region.region.RegionMultiPeriodOptimization', TrackingOptimization)
    monkeypatch.setattr('region.region.RegionResultApplier', Mock())

    context = Mock()
    context.simulation_options = {'optimization_type': OptimizationType.REGION_MULTI_PERIOD}
    sut.optimize(2030, context)

    # Optimization should be skipped
    assert calls['optimization_called'] is False


def test_optimize_with_multi_period_creates_optimization(monkeypatch, sut):
    """Test optimize creates RegionMultiPeriodOptimization for multi-period type."""
    from optimization.region_multi_period_optimization_result import (
        RegionMultiPeriodOptimizationResult,
    )

    class _ProductionUnit:
        def _remove_inactive_sub_production_units(self, year):
            pass

        def _process_option_to_sub_production_unit_mapping(self):
            return {}

    pu1 = _ProductionUnit()
    sut.sites = [Mock(production_units=[pu1])]
    sut._cached_multi_period_result = None

    calls = {'optimization_type': None, 'applied': False}

    class FakeMultiPeriodOptimization:
        def __init__(self, year, region, production_units, context):
            calls['optimization_type'] = 'multi_period'

        def optimize(self):
            # Return a multi-period result
            result = Mock(spec=RegionMultiPeriodOptimizationResult)
            result.has_result_for_year.return_value = True
            return result

    class FakeApplier:
        def apply_for_year(self, year, region_result, production_units, context):
            calls['applied'] = True

    monkeypatch.setattr('region.region.RegionMultiPeriodOptimization', FakeMultiPeriodOptimization)
    monkeypatch.setattr('region.region.RegionResultApplier', FakeApplier)

    context = Mock()
    context.simulation_options = {'optimization_type': OptimizationType.REGION_MULTI_PERIOD}
    sut.optimize(2030, context)

    assert calls['optimization_type'] == 'multi_period'
    assert calls['applied'] is True
    assert sut._cached_multi_period_result is not None


def test_replay_cached_multi_period_result(monkeypatch, sut):
    """Test _replay_cached_result applies cached multi-period result for year."""
    from optimization.region_multi_period_optimization_result import (
        RegionMultiPeriodOptimizationResult,
    )

    class _ProductionUnit:
        def _remove_inactive_sub_production_units(self, year):
            self.removed_year = year

        def _process_option_to_sub_production_unit_mapping(self):
            return {'mapping': 'value'}

    pu1 = _ProductionUnit()
    sut._cached_production_units = [pu1]
    sut._cached_multi_period_result = Mock(spec=RegionMultiPeriodOptimizationResult)

    calls = {'applied': False}

    class FakeApplier:
        def apply_for_year(self, year, result, production_units, context):
            calls['applied'] = True
            calls['year'] = year
            calls['result'] = result

    monkeypatch.setattr('region.region.RegionResultApplier', FakeApplier)

    context = Mock()
    sut._replay_cached_result(2030, context)

    assert calls['applied'] is True
    assert calls['year'] == 2030
    assert pu1.removed_year == 2030
