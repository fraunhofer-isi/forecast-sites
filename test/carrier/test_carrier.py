# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from carrier.carrier import Carrier


class TestCarrier:
    """Test the Carrier base class."""

    def test_carrier_initialization(self):
        """Carrier should initialize with id and name."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        assert carrier.id == 1
        assert carrier.name == 'Electricity'

    def test_carrier_id_is_readonly(self):
        """Carrier id should be read-only property."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(AttributeError):
            carrier.id = 2

    def test_carrier_repr(self):
        """Carrier should have proper repr."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        assert repr(carrier) == 'Carrier(1, Electricity)'

    def test_carrier_unit_not_implemented(self):
        """Unit property should raise NotImplementedError in base class."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            _ = carrier.unit

    def test_carrier_maximum_production_not_implemented(self):
        """maximum_production_in_unit should raise NotImplementedError."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            _ = carrier.maximum_production_in_unit

    def test_carrier_minimum_use_not_implemented(self):
        """minimum_use_in_unit should raise NotImplementedError."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            carrier.minimum_use_in_unit(_year=2025, _simulation_options={})

    def test_carrier_purchase_price_not_implemented(self):
        """purchase_price_in_euro_per_unit should raise NotImplementedError."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            carrier.purchase_price_in_euro_per_unit(_year=2025)

    def test_carrier_sell_price_not_implemented(self):
        """sell_price_in_euro_per_unit should raise NotImplementedError."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            carrier.sell_price_in_euro_per_unit(_year=2025)

    def test_carrier_upstream_emission_not_implemented(self):
        """upstream_emission_in_t_co2_per_unit should raise NotImplementedError."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            carrier.upstream_emission_in_t_co2_per_unit(_year=2025, _simulation_options={})

    def test_carrier_downstream_emission_not_implemented(self):
        """downstream_emission_in_t_co2_per_unit should raise NotImplementedError."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            carrier.downstream_emission_in_t_co2_per_unit(_year=2025, _simulation_options={})

    def test_carrier_renewably_bound_co2_not_implemented(self):
        """renewably_bound_co2_emission_in_t_co2_per_unit should raise NotImplementedError."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            carrier.renewably_bound_co2_emission_in_t_co2_per_unit(_year=2025, _simulation_options={})

    def test_carrier_taxes_default_to_zero(self):
        """Base carrier taxes should default to zero."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        assert carrier.taxes_in_euro_per_unit(_year=2025, _simulation_options={}) == 0.0

    def test_carrier_subsidies_default_to_zero(self):
        """Base carrier subsidies should default to zero."""
        carrier = Carrier(carrier_id=1, name='Electricity')
        assert carrier.subsidies_in_euro_per_unit(_year=2025, _simulation_options={}) == 0.0

    def test_check_for_non_existing_interim_year_valid(self):
        """Should not raise for year >= last_year_str."""
        Carrier._check_for_non_exiting_interim_year(2025, '2020')

    def test_check_for_non_existing_interim_year_same(self):
        """Should not raise for year == last_year_str."""
        Carrier._check_for_non_exiting_interim_year(2025, '2025')

    def test_check_for_non_existing_interim_year_invalid(self):
        """Should raise KeyError for year < last_year_str."""
        with pytest.raises(KeyError, match='Year 2020 not found in data'):
            Carrier._check_for_non_exiting_interim_year(2020, '2025')

    def test_multiple_carriers(self):
        """Multiple carriers should be independent."""
        carrier1 = Carrier(carrier_id=1, name='Electricity')
        carrier2 = Carrier(carrier_id=2, name='Natural Gas')

        assert carrier1.id == 1
        assert carrier2.id == 2
        assert carrier1.name == 'Electricity'
        assert carrier2.name == 'Natural Gas'
        assert carrier1 != carrier2
