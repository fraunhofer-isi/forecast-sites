# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


import pytest
from pandas import DataFrame
from test_utils.isi_mock import Mock, patch

from optimization.optimization_context import OptimizationContext
from sites.site import Site


@pytest.fixture
def sut():
    id_site = 1
    region = Mock()
    geometry = Mock()
    production_units = _production_unit_mocks()
    processes = []

    site = Site(
        id_site,
        region,
        geometry,
        processes,
    )
    site.production_units = production_units
    return site


def _production_unit_mocks():
    production_units = [Mock(), Mock(), Mock()]
    index = 1
    for production_unit in production_units:
        process = Mock()
        process.id = index
        production_unit.process = process
        production_unit.used_process_ids = [index]
        production_unit.probability_of_change.return_value = 1
        production_unit.number_of_process_usages.return_value = 1
        production_unit.optimize = Mock('mocked_optimization_result')
        index += 1
    return production_units


def test_construction(sut):
    assert sut is not None


def test_used_process_ids(sut):
    process_ids = sut.used_process_ids
    assert process_ids == [1, 2, 3]


def test_sectors(sut):
    sectors = sut.sectors
    assert len(sectors) == 3


@patch(Site._initialize_pipeline_context, 'mocked_pipeline_context')
@patch(OptimizationContext.__init__, None)
def test_initialize_context(sut):
    simulation = Mock()
    sut.initialize_context(simulation)
    assert sut.pipeline_context == 'mocked_pipeline_context'


def test_optimize(sut):
    sut.optimize(2015)
    for production_unit in sut.production_units:
        assert production_unit.optimize.called


def test_can_purchase_blocks_h2_when_not_accessible(sut):
    sut.pipeline_context = {'distance_to_closest_h2_pipeline_in_km': None}
    carrier = Mock()
    carrier.name = 'H2'

    result = sut.can_purchase(carrier)

    assert result is False


def test_can_purchase_blocks_renewable_h2_when_not_accessible(sut):
    # Renewable H2 must be blocked by the same 50 km rule as regular H2
    sut.pipeline_context = {'distance_to_closest_h2_pipeline_in_km': None}
    carrier = Mock()
    carrier.name = 'Renewable H2'

    result = sut.can_purchase(carrier)

    assert result is False


def test_accept(sut):
    visitor = Mock()
    year = 2015
    sut.accept(visitor, year)
    assert visitor.enter_site.called

    for production_unit in sut.production_units:
        assert production_unit.accept.called is True

    assert visitor.exit_site.called


def test_number_of_process_usage(sut):
    process = Mock()
    assert sut.number_of_process_usages(process) == 3


class TestIsHydrogenCarrier:
    def _carrier(self, name):
        carrier = Mock()
        carrier.name = name
        return carrier

    def test_h2(self, sut):
        assert sut._is_hydrogen_carrier(self._carrier('H2')) is True

    def test_hydrogen(self, sut):
        assert sut._is_hydrogen_carrier(self._carrier('Hydrogen')) is True

    def test_renewable_h2(self, sut):
        assert sut._is_hydrogen_carrier(self._carrier('Renewable H2')) is True

    def test_case_insensitive(self, sut):
        assert sut._is_hydrogen_carrier(self._carrier('renewable h2')) is True

    def test_non_hydrogen(self, sut):
        carrier = self._carrier('Natural Gas')
        assert sut._is_hydrogen_carrier(carrier) is False

    def test_electricity(self, sut):
        carrier = self._carrier('Electricity')
        assert sut._is_hydrogen_carrier(carrier) is False


class TestCarrierAvailability:
    class TestH2:
        @patch(Site._h2_is_accessible, True)
        def test_accessible(self, sut):
            sut._region.carrier_availability = Mock(22)

            carrier = Mock()
            carrier.name = 'H2'

            result = sut.carrier_availability(carrier, 2015)
            assert result == 22

        @patch(Site._h2_is_accessible, False)
        def test_not_accessible(self, sut):
            carrier = Mock()
            carrier.name = 'H2'

            result = sut.carrier_availability(carrier, 2015)
            assert result == 0

    class TestRenewableH2:
        @patch(Site._h2_is_accessible, True)
        def test_accessible(self, sut):
            sut._region.carrier_availability = Mock(22)

            carrier = Mock()
            carrier.name = 'Renewable H2'

            result = sut.carrier_availability(carrier, 2015)
            assert result == 22

        @patch(Site._h2_is_accessible, False)
        def test_not_accessible(self, sut):
            # Renewable H2 is unavailable beyond 50 km, same as regular H2
            carrier = Mock()
            carrier.name = 'Renewable H2'

            result = sut.carrier_availability(carrier, 2015)
            assert result == 0

    def test_other_carrier(self, sut):
        sut._region.carrier_availability = Mock(33)

        carrier = Mock()
        carrier.name = 'Natural Gas'

        result = sut.carrier_availability(carrier, 2015)
        assert result == 33


def test_consume_purchased_carrier_amounts_for_start_year(sut):
    sut.consume_purchased_carrier_amounts_for_start_year(2020)
    for production_unit in sut.production_units:
        assert production_unit.consume_purchased_carrier_amounts.called


def test_consume_purchased_carrier_amount(sut):
    sut.consume_purchased_carrier_amount('mocked_carrier', 10, 2020, 'mocked_context')
    assert sut.pool.consume_purchased_carrier_amount.called


# provide_produced_carrier_amounts_for_start_year removed - test deleted
# provide_produced_carrier_amount removed - test deleted


class TestH2IsAccessible:
    def test_none(self, sut):
        sut.pipeline_context = {'distance_to_closest_h2_pipeline_in_km': None}
        result = sut._h2_is_accessible()
        assert result is False

    def test_larger(self, sut):
        sut.pipeline_context = {'distance_to_closest_h2_pipeline_in_km': 51}
        result = sut._h2_is_accessible()
        assert result is False

    def test_smaller(self, sut):
        sut.pipeline_context = {'distance_to_closest_h2_pipeline_in_km': 49}
        result = sut._h2_is_accessible()
        assert result is True


class TestCanPurchaseYearAware:
    """Year-aware can_purchase: backward-compat + future H2 backbone expansion."""

    def _h2_carrier(self):
        carrier = Mock()
        carrier.name = 'H2'
        return carrier

    def test_without_year_uses_pipeline_context_backward_compat(self, sut):
        """Without year, falls back to pipeline_context (backward-compatible path)."""
        sut.pipeline_context = {'distance_to_closest_h2_pipeline_in_km': 49}
        sut._h2_first_accessible_year = None

        result = sut.can_purchase(self._h2_carrier())

        assert result is True

    def test_with_year_before_accessible_year_returns_false(self, sut):
        """H2 not accessible before pipeline commissioning year."""
        sut._h2_first_accessible_year = 2030

        result = sut.can_purchase(self._h2_carrier(), year=2025)

        assert result is False

    def test_with_year_at_accessible_year_returns_true(self, sut):
        """H2 accessible from the commissioning year onward."""
        sut._h2_first_accessible_year = 2030

        result = sut.can_purchase(self._h2_carrier(), year=2030)

        assert result is True


@patch(
    Site._distance_to_closest_h2_pipeline_in_km,
    'mocked_distance_to_closest_h2_pipeline',
)
def test_initialize_pipeline_context(sut):
    simulation = Mock()
    context = sut._initialize_pipeline_context(simulation)
    assert context['distance_to_closest_h2_pipeline_in_km'] == 'mocked_distance_to_closest_h2_pipeline'


@patch(Site._determine_distance_to_closest_h2_pipeline_in_km, 'mocked_distance')
def test_distance_to_closest_h2_pipeline(sut):
    simulation = Mock()
    simulation.is_recognizing_pipelines = True
    result = sut._distance_to_closest_h2_pipeline_in_km(simulation)
    assert result == 'mocked_distance'

    simulation.is_recognizing_pipelines = False
    result = sut._distance_to_closest_h2_pipeline_in_km(simulation)
    assert result == 0


class TestDetermineDistanceToClosestH2Pipeline:
    mocked_pipeline_site_relations_with_h2 = DataFrame(
        [
            {'site': 1, 'pipeline': 1, 'distance': 2, 'mode': 'H2'},
            {'site': 1, 'pipeline': 2, 'distance': 4, 'mode': 'H2'},
            {'site': 1, 'pipeline': 1, 'distance': 4, 'mode': 'CO2'},
        ]
    ).set_index(['site', 'pipeline'])

    mocked_pipeline_site_relations_without_h2 = DataFrame(
        [
            {'site': 1, 'pipeline': 1, 'distance': 0, 'mode': ''},
        ]
    ).set_index(['site', 'pipeline'])

    @patch(Site._pipeline_site_relations, mocked_pipeline_site_relations_with_h2)
    def test_with_h2_pipeline(self, sut):
        simulation = Mock()
        result = sut._determine_distance_to_closest_h2_pipeline_in_km(simulation)
        assert result == 2

    @patch(Site._pipeline_site_relations, mocked_pipeline_site_relations_without_h2)
    def test_without_h2_pipeline(self, sut):
        simulation = Mock()
        result = sut._determine_distance_to_closest_h2_pipeline_in_km(simulation)
        assert result is None


def test_pipeline_site_relations(sut):
    simulation = Mock()
    simulation.pipeline_site_relations = DataFrame(
        [
            {'site': 1, 'pipeline': 1, 'distance': 2, 'mode': 'H2'},
            {'site': 2, 'pipeline': 2, 'distance': 4, 'mode': 'H2'},
            {'site': 1, 'pipeline': 1, 'distance': 4, 'mode': 'CO2'},
        ]
    ).set_index(['site', 'pipeline'])
    result = sut._pipeline_site_relations(simulation)
    assert result is not None
    assert len(result) == 2


def test_can_purchase_non_h2_carrier_always_allowed(sut):
    """Test that non-H2 carriers can always be purchased (line 64)."""
    carrier = Mock()
    carrier.name = 'Natural Gas'  # Not H2

    result = sut.can_purchase(carrier)

    # Non-H2 carriers always return True
    assert result is True


def test_initialize_context_skips_pipeline_when_skip_flag_set(sut):
    """Test that pipeline initialization is skipped when _skip_pipeline_init is True (line 44->47)."""
    sut._skip_pipeline_init = True

    simulation = Mock()
    simulation.is_recognizing_pipelines = True

    # Mock region for optimization context
    sut._region.co2_cost_in_euro_per_t_co2 = 100
    sut._region.interest_rate = 0.05
    simulation.options = {}

    sut.initialize_context(simulation)

    # Pipeline context should NOT be set (remains None because we skipped initialization)
    assert sut.pipeline_context is None
    # But optimization context SHOULD be set
    assert sut._optimization_context is not None


def test_compute_h2_first_accessible_year_when_pipelines_not_recognized(sut):
    """Test that None is returned when pipelines aren't being recognized (line 134)."""
    simulation = Mock()
    simulation.is_recognizing_pipelines = False  # Pipelines not recognized

    result = sut._compute_h2_first_accessible_year(simulation)

    assert result is None


def test_compute_h2_first_accessible_year_with_multiple_pipelines(sut):
    """Test iteration over multiple pipelines to find earliest accessible year (lines 142-148)."""
    simulation = Mock()
    simulation.is_recognizing_pipelines = True

    # Create mock pipeline dataframe
    pipelines_df = DataFrame({'Commissioning Year First': [2030, 2025, 2035]}, index=[1, 2, 3])
    simulation.pipelines.pipelines_df = pipelines_df

    # Mock pipeline_site_relations - multiple pipelines at various distances
    pipeline_site_relations = DataFrame(
        [
            {'site': 1, 'pipeline': 1, 'distance': 60, 'mode': 'H2'},  # Outside threshold
            {'site': 1, 'pipeline': 2, 'distance': 30, 'mode': 'H2'},  # Inside - 2025
            {'site': 1, 'pipeline': 3, 'distance': 40, 'mode': 'H2'},  # Inside - 2035
        ]
    ).set_index(['site', 'pipeline'])
    sut._pipeline_site_relations = Mock(return_value=pipeline_site_relations)

    result = sut._compute_h2_first_accessible_year(simulation)

    # Should return earliest accessible year (2025 from pipeline 2)
    assert result == 2025
