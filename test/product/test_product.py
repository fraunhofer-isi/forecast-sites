# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import patch

import pytest

from carrier.carrier_unit import CarrierUnit
from product.product import Product


class TestProduct:
    """Test the Product carrier class."""

    @pytest.fixture
    def product_data(self):
        """Create product data dict."""
        return {
            'purchase_price_in_euro_per_t': {'2020': 100.0, '2025': 110.0, '2030': 120.0},
            'sell_price_in_euro_per_t': {'2020': 150.0, '2025': 160.0, '2030': 170.0},
            'upstream_emission_start_year_in_t_co2_per_t': 2.0,
            'upstream_emission_end_year_in_t_co2_per_t': 1.5,
            'downstream_emission_in_t_co2_per_t': 0.5,
            'maximum_production_in_t': 2000.0,
        }

    def test_initialization(self, product_data):
        """Should initialize with ID, name, and data."""
        product = Product(1, 'Steel', product_data)
        assert product.id == 1
        assert product.name == 'Steel'

    def test_unit_is_tonnes(self, product_data):
        """Should return CarrierUnit.T as unit."""
        product = Product(1, 'Steel', product_data)
        assert product.unit == CarrierUnit.T

    def test_maximum_production_in_unit(self, product_data):
        """Should return maximum production."""
        product = Product(1, 'Steel', product_data)
        assert product.maximum_production_in_unit == 2000.0

    def test_downstream_emission_ignores_year_and_emission_constraint_scope(self, product_data):
        """
        Pins the deliberate scope asymmetry, confirmed by the domain owner in
        `bd show forecast-sites-private-6zj.11`.

        The objective function prices downstream CO2 *unconditionally*, while only the
        emission CONSTRAINT honors `emission_constraint_scope`. Taking 'downstream' out
        of the scope therefore drops the constraint but leaves the price signal intact.
        That asymmetry is exactly why both parameters are declared unused, as `_year`
        and `_simulation_options`. Do not make this scope-aware.
        """
        product = Product(1, 'Steel', product_data)

        inside_scope = product.downstream_emission_in_t_co2_per_unit(
            2020,
            {'emission_constraint_scope': frozenset({'direct', 'downstream'})},
        )
        outside_scope = product.downstream_emission_in_t_co2_per_unit(
            2050,
            {'emission_constraint_scope': frozenset({'direct'})},
        )

        assert outside_scope == inside_scope
        assert outside_scope != 0  # otherwise the equality above would be vacuous

    def test_minimum_use_is_zero(self, product_data):
        """Should always return 0 for minimum use."""
        product = Product(1, 'Steel', product_data)
        assert product.minimum_use_in_unit(2025, {}) == 0

    def test_purchase_price_exact_year(self, product_data):
        """Should return price for exact year match."""
        product = Product(1, 'Steel', product_data)
        assert product.purchase_price_in_euro_per_t(2025) == 110.0

    def test_purchase_price_defaults_to_last_year(self, product_data):
        """Should return last year's price for years beyond data."""
        product = Product(1, 'Steel', product_data)
        assert product.purchase_price_in_euro_per_t(2035) == 120.0

    def test_purchase_price_per_unit(self, product_data):
        """Should return price per unit (same as per tonne)."""
        product = Product(1, 'Steel', product_data)
        assert product.purchase_price_in_euro_per_unit(2025) == 110.0

    def test_purchase_cost_calculation(self, product_data):
        """Should calculate total purchase cost."""
        product = Product(1, 'Steel', product_data)
        cost = product.purchase_cost_in_euro(50.0, 2025)
        assert cost == 5500.0  # 50 tonnes * 110 euro/tonne

    def test_sell_price_exact_year(self, product_data):
        """Should return sell price for exact year match."""
        product = Product(1, 'Steel', product_data)
        assert product.sell_price_in_euro_per_t(2025) == 160.0

    def test_sell_price_defaults_to_last_year(self, product_data):
        """Should return last year's sell price for years beyond data."""
        product = Product(1, 'Steel', product_data)
        assert product.sell_price_in_euro_per_t(2035) == 170.0

    def test_sell_price_per_unit(self, product_data):
        """Should return sell price per unit (same as per tonne)."""
        product = Product(1, 'Steel', product_data)
        assert product.sell_price_in_euro_per_unit(2025) == 160.0

    def test_downstream_emission_constant(self, product_data):
        """Should return constant downstream emission."""
        product = Product(1, 'Steel', product_data)
        assert product.downstream_emission_in_t_co2_per_unit(2025, {}) == 0.5

    def test_renewably_bound_co2_emission_is_zero(self, product_data):
        """Should return 0 for renewably bound CO2 emission."""
        product = Product(1, 'Steel', product_data)
        assert product.renewably_bound_co2_emission_in_t_co2_per_unit(2025, {}) == 0

    def test_upstream_emission_interpolation(self, product_data):
        """Should interpolate upstream emission."""
        with patch('product.product.interpolator.interpolate', return_value=1.75):
            product = Product(1, 'Steel', product_data)
            emission = product.upstream_emission_in_t_co2_per_t(2025, {'start_year': 2020})
            assert emission == 1.75

    def test_upstream_emission_per_unit(self, product_data):
        """Should return upstream emission per unit (same as per tonne)."""
        with patch('product.product.interpolator.interpolate', return_value=1.75):
            product = Product(1, 'Steel', product_data)
            emission = product.upstream_emission_in_t_co2_per_unit(2025, {'start_year': 2020})
            assert emission == 1.75
