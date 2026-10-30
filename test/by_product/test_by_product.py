# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import patch

import pytest

from by_product.by_product import ByProduct
from carrier.carrier_unit import CarrierUnit


class TestByProduct:
    """Test the ByProduct carrier class."""

    @pytest.fixture
    def by_product_data(self):
        """Create by-product data dict."""
        return {
            'purchase_price_in_euro_per_t': {'2020': 10.0, '2025': 12.0, '2030': 15.0},
            'sell_price_in_euro_per_t': {'2020': 20.0, '2025': 22.0, '2030': 25.0},
            'upstream_emission_start_year_in_t_co2_per_t': 5.0,
            'upstream_emission_end_year_in_t_co2_per_t': 3.0,
            'downstream_emission_in_t_co2_per_t': 2.0,
            'renewably_bound_co2_emission_in_t_co2_per_t': 1.0,
            'maximum_production_in_t': 1000.0,
        }

    def test_initialization(self, by_product_data):
        """Should initialize with ID, name, and data."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.id == 1
        assert by_product.name == 'Steel Scrap'

    def test_unit_is_tonnes(self, by_product_data):
        """Should return CarrierUnit.T as unit."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.unit == CarrierUnit.T

    def test_maximum_production_in_unit(self, by_product_data):
        """Should return maximum production."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.maximum_production_in_unit == 1000.0

    def test_downstream_emission_ignores_year_and_emission_constraint_scope(self, by_product_data):
        """
        Pins the deliberate scope asymmetry, confirmed by the domain owner in
        `bd show forecast-sites-private-6zj.11`.

        The objective function prices downstream CO2 *unconditionally*, while only the
        emission CONSTRAINT honors `emission_constraint_scope`. Taking 'downstream' out
        of the scope therefore drops the constraint but leaves the price signal intact.
        That asymmetry is exactly why both parameters are declared unused, as `_year`
        and `_simulation_options`. Do not make this scope-aware.
        """
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)

        inside_scope = by_product.downstream_emission_in_t_co2_per_unit(
            2020,
            {'emission_constraint_scope': frozenset({'direct', 'downstream'})},
        )
        outside_scope = by_product.downstream_emission_in_t_co2_per_unit(
            2050,
            {'emission_constraint_scope': frozenset({'direct'})},
        )

        assert outside_scope == inside_scope
        assert outside_scope != 0  # otherwise the equality above would be vacuous

    def test_minimum_use_is_zero(self, by_product_data):
        """Should always return 0 for minimum use."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.minimum_use_in_unit(2025, {}) == 0
        assert by_product.minimum_use_in_unit(2030, {}) == 0

    def test_purchase_price_exact_year(self, by_product_data):
        """Should return price for exact year match."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.purchase_price_in_euro_per_t(2025) == 12.0

    def test_purchase_price_defaults_to_last_year(self, by_product_data):
        """Should return last year's price for years beyond data."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.purchase_price_in_euro_per_t(2035) == 15.0

    def test_purchase_price_per_unit(self, by_product_data):
        """Should return price per unit (same as per tonne)."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.purchase_price_in_euro_per_unit(2025) == 12.0

    def test_purchase_cost_calculation(self, by_product_data):
        """Should calculate total purchase cost."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        cost = by_product.purchase_cost_in_euro(100.0, 2025)
        assert cost == 1200.0  # 100 tonnes * 12 euro/tonne

    def test_sell_price_exact_year(self, by_product_data):
        """Should return sell price for exact year match."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.sell_price_in_euro_per_t(2025) == 22.0

    def test_sell_price_defaults_to_last_year(self, by_product_data):
        """Should return last year's sell price for years beyond data."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.sell_price_in_euro_per_t(2035) == 25.0

    def test_sell_price_per_unit(self, by_product_data):
        """Should return sell price per unit (same as per tonne)."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.sell_price_in_euro_per_unit(2025) == 22.0

    def test_downstream_emission_constant(self, by_product_data):
        """Should return constant downstream emission."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.downstream_emission_in_t_co2_per_unit(2025, {}) == 2.0
        assert by_product.downstream_emission_in_t_co2_per_unit(2030, {}) == 2.0

    def test_renewably_bound_co2_emission(self, by_product_data):
        """Should return renewably bound CO2 emission."""
        by_product = ByProduct(1, 'Steel Scrap', by_product_data)
        assert by_product.renewably_bound_co2_emission_in_t_co2_per_unit(2025, {}) == 1.0

    def test_renewably_bound_co2_defaults_to_zero(self):
        """Should default to 0 if not provided."""
        data = {
            'purchase_price_in_euro_per_t': {'2020': 10.0},
            'sell_price_in_euro_per_t': {'2020': 20.0},
            'upstream_emission_start_year_in_t_co2_per_t': 5.0,
            'upstream_emission_end_year_in_t_co2_per_t': 3.0,
            'downstream_emission_in_t_co2_per_t': 2.0,
            'maximum_production_in_t': 1000.0,
        }
        by_product = ByProduct(1, 'Steel Scrap', data)
        assert by_product.renewably_bound_co2_emission_in_t_co2_per_unit(2025, {}) == 0

    def test_upstream_emission_interpolation(self, by_product_data):
        """Should interpolate upstream emission."""
        with patch('by_product.by_product.interpolator.interpolate', return_value=4.0):
            by_product = ByProduct(1, 'Steel Scrap', by_product_data)
            emission = by_product.upstream_emission_in_t_co2_per_t(2025, {'start_year': 2020})
            assert emission == 4.0

    def test_upstream_emission_per_unit(self, by_product_data):
        """Should return upstream emission per unit (same as per tonne)."""
        with patch('by_product.by_product.interpolator.interpolate', return_value=4.0):
            by_product = ByProduct(1, 'Steel Scrap', by_product_data)
            emission = by_product.upstream_emission_in_t_co2_per_unit(2025, {'start_year': 2020})
            assert emission == 4.0
