# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import patch

import pytest

from carrier.carrier_unit import CarrierUnit
from energy_carrier.energy_carrier import EnergyCarrier


class TestEnergyCarrier:
    """Test the EnergyCarrier class."""

    @pytest.fixture
    def energy_carrier_data(self):
        """Create energy carrier data dict."""
        return {
            'purchase_price_in_euro_per_gj': {'2020': 5.0, '2025': 6.0, '2030': 7.0},
            'sell_price_in_euro_per_gj': {'2020': 10.0, '2025': 11.0, '2030': 12.0},
            'direct_emission_in_t_co2_per_gj': 0.3,
            'maximum_production_in_gj': 5000.0,
            'upstream_emission_start_year_in_t_co2_per_gj': 0.1,
            'upstream_emission_end_year_in_t_co2_per_gj': 0.05,
            'renewably_bound_co2_emission_in_t_co2_per_gj': 0.02,
            'minimum_use_start_year_in_gj': 100.0,
            'minimum_use_end_year_in_gj': 200.0,
            'subsidies_start_year_in_euro_per_gj': 1.0,
            'subsidies_end_year_in_euro_per_gj': 0.5,
            'subsidies_interim_year_in_euro_per_gj': 0.75,
            'taxes_start_year_in_euro_per_gj': 0.2,
            'taxes_end_year_in_euro_per_gj': 0.3,
        }

    def test_initialization(self, energy_carrier_data):
        """Should initialize with ID, name, and data."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.id == 1
        assert carrier.name == 'Natural Gas'

    def test_unit_is_gj(self, energy_carrier_data):
        """Should return CarrierUnit.GJ as unit."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.unit == CarrierUnit.GJ

    def test_direct_emission_property(self, energy_carrier_data):
        """Should return direct emission."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.direct_emission_in_t_co2_per_gj == 0.3

    def test_downstream_emission_ignores_year_and_emission_constraint_scope(self, energy_carrier_data):
        """
        Pins the deliberate scope asymmetry, confirmed by the domain owner in
        `bd show forecast-sites-private-6zj.11`.

        The objective function prices downstream CO2 *unconditionally*, while only the
        emission CONSTRAINT honors `emission_constraint_scope`. Taking 'downstream' out
        of the scope therefore drops the constraint but leaves the price signal intact.
        That asymmetry is exactly why both parameters are declared unused, as `_year`
        and `_simulation_options`. Do not make this scope-aware.
        """
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)

        inside_scope = carrier.downstream_emission_in_t_co2_per_unit(
            2020,
            {'emission_constraint_scope': frozenset({'direct', 'downstream'})},
        )
        outside_scope = carrier.downstream_emission_in_t_co2_per_unit(
            2050,
            {'emission_constraint_scope': frozenset({'direct'})},
        )

        assert outside_scope == inside_scope
        assert outside_scope != 0  # otherwise the equality above would be vacuous

    def test_maximum_production_in_unit(self, energy_carrier_data):
        """Should return maximum production in GJ."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.maximum_production_in_unit == 5000.0

    def test_purchase_price_exact_year(self, energy_carrier_data):
        """Should return purchase price for exact year match."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.purchase_price_in_euro_per_gj(2025) == 6.0

    def test_purchase_price_defaults_to_last_year(self, energy_carrier_data):
        """Should return last year's price for years beyond data."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.purchase_price_in_euro_per_gj(2035) == 7.0

    def test_purchase_price_per_unit(self, energy_carrier_data):
        """Should return purchase price per unit (same as per GJ)."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.purchase_price_in_euro_per_unit(2025) == 6.0

    def test_purchase_cost_calculation(self, energy_carrier_data):
        """Should calculate total purchase cost."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        cost = carrier.purchase_cost_in_euro(100.0, 2025)
        assert cost == 600.0  # 100 GJ * 6 euro/GJ

    def test_sell_price_exact_year(self, energy_carrier_data):
        """Should return sell price for exact year match."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.sell_price_in_euro_per_gj(2025) == 11.0

    def test_sell_price_defaults_to_last_year(self, energy_carrier_data):
        """Should return last year's sell price for years beyond data."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.sell_price_in_euro_per_gj(2035) == 12.0

    def test_sell_price_per_unit(self, energy_carrier_data):
        """Should return sell price per unit (same as per GJ)."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.sell_price_in_euro_per_unit(2025) == 11.0

    def test_downstream_emission_equals_direct_emission(self, energy_carrier_data):
        """Should default downstream_emission to direct_emission."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.downstream_emission_in_t_co2_per_unit(2025, {}) == 0.3

    def test_downstream_emission_can_override(self):
        """Should allow override of downstream emission."""
        data = {
            'purchase_price_in_euro_per_gj': {'2020': 5.0},
            'sell_price_in_euro_per_gj': {'2020': 10.0},
            'direct_emission_in_t_co2_per_gj': 0.3,
            'downstream_emission_in_t_co2_per_gj': 0.4,
            'maximum_production_in_gj': 5000.0,
            'upstream_emission_start_year_in_t_co2_per_gj': 0.1,
            'upstream_emission_end_year_in_t_co2_per_gj': 0.05,
            'renewably_bound_co2_emission_in_t_co2_per_gj': 0.02,
            'minimum_use_start_year_in_gj': 100.0,
            'minimum_use_end_year_in_gj': 200.0,
            'subsidies_start_year_in_euro_per_gj': 1.0,
            'subsidies_end_year_in_euro_per_gj': 0.5,
            'subsidies_interim_year_in_euro_per_gj': 0.75,
            'taxes_start_year_in_euro_per_gj': 0.2,
            'taxes_end_year_in_euro_per_gj': 0.3,
        }
        carrier = EnergyCarrier(1, 'Natural Gas', data)
        assert carrier.downstream_emission_in_t_co2_per_unit(2025, {}) == 0.4

    def test_renewably_bound_co2_emission(self, energy_carrier_data):
        """Should return renewably bound CO2 emission."""
        carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
        assert carrier.renewably_bound_co2_emission_in_t_co2_per_unit(2025, {}) == 0.02

    def test_upstream_emission_interpolation(self, energy_carrier_data):
        """Should interpolate upstream emission."""
        with patch('energy_carrier.energy_carrier.interpolator.interpolate', return_value=0.075):
            carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
            emission = carrier.upstream_emission_in_t_co2_per_gj(2025, {'start_year': 2020})
            assert emission == 0.075

    def test_upstream_emission_per_unit(self, energy_carrier_data):
        """Should return upstream emission per unit (same as per GJ)."""
        with patch('energy_carrier.energy_carrier.interpolator.interpolate', return_value=0.075):
            carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
            emission = carrier.upstream_emission_in_t_co2_per_unit(2025, {'start_year': 2020})
            assert emission == 0.075

    def test_minimum_use_interpolation(self, energy_carrier_data):
        """Should interpolate minimum use."""
        with patch('energy_carrier.energy_carrier.interpolator.interpolate', return_value=150.0):
            carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
            min_use = carrier.minimum_use_in_unit(2025, {'start_year': 2020})
            assert min_use == 150.0

    def test_subsidies_interpolation(self, energy_carrier_data):
        """Should interpolate subsidies using interpolate_cost."""
        with patch('energy_carrier.energy_carrier.interpolator.interpolate_cost', return_value=0.75):
            carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
            subsidies = carrier.subsidies_in_euro_per_gj(2025, {'start_year': 2020})
            assert subsidies == 0.75

    def test_subsidies_per_unit(self, energy_carrier_data):
        """Should return subsidies per unit using the per-GJ value."""
        with patch('energy_carrier.energy_carrier.interpolator.interpolate_cost', return_value=0.75):
            carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
            subsidies = carrier.subsidies_in_euro_per_unit(2025, {'start_year': 2020})
            assert subsidies == 0.75

    def test_taxes_interpolation(self, energy_carrier_data):
        """Should interpolate taxes."""
        with patch('energy_carrier.energy_carrier.interpolator.interpolate', return_value=0.25):
            carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
            taxes = carrier.taxes_in_euro_per_gj(2025, {'start_year': 2020})
            assert taxes == 0.25

    def test_taxes_per_unit(self, energy_carrier_data):
        """Should return taxes per unit using the per-GJ value."""
        with patch('energy_carrier.energy_carrier.interpolator.interpolate', return_value=0.25):
            carrier = EnergyCarrier(1, 'Natural Gas', energy_carrier_data)
            taxes = carrier.taxes_in_euro_per_unit(2025, {'start_year': 2020})
            assert taxes == 0.25
