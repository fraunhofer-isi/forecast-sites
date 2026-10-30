# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from energy_carrier.energy_carrier import EnergyCarrier


class EnergyCarrierFactory:
    def __init__(self, data_interface):
        self._energy_carrier_data = data_interface.energy_carrier_data

        self._purchase_price = data_interface.energy_carrier_purchase_price

        self._sell_price = data_interface.energy_carrier_sell_price

        self._minimum_use = data_interface.energy_carrier_minimum_use

        self._emission = data_interface.energy_carrier_emission

        self._subsidies = data_interface.energy_carrier_subsidies

        self._taxes = data_interface.energy_carrier_taxes

        self._maximum_production = data_interface.energy_carrier_maximum_production

    def create_map(self):
        energy_carrier_map = {}
        for _, row in self._energy_carrier_data.iterrows():
            id_energy_carrier = row['id']
            name = row['name']
            energy_carrier_map[id_energy_carrier] = self._energy_carrier(id_energy_carrier, name)
        return energy_carrier_map

    def _energy_carrier(self, id_energy_carrier, name):
        emission = self._emission.loc[id_energy_carrier]
        direct_emission_in_t_per_gj = emission['direct_emission_in_t_co2_per_gj']

        upstream_emission_start_year_in_t_co2_per_gj = emission['upstream_emission_start_year_in_t_co2_per_gj']
        upstream_emission_end_year_in_t_co2_per_gj = emission['upstream_emission_end_year_in_t_co2_per_gj']

        renewably_bound_co2_emission_in_t_co2_per_gj = emission['renewably_bound_co2_emission_in_t_co2_per_gj']

        subsidies = self._subsidies.loc[id_energy_carrier]
        subsidies_start_year_in_euro_per_gj = subsidies['subsidies_start_year_in_euro_per_gj']
        subsidies_interim_year_in_euro_per_gj = subsidies['subsidies_interim_year_in_euro_per_gj']
        subsidies_end_year_in_euro_per_gj = subsidies['subsidies_end_year_in_euro_per_gj']

        taxes = self._taxes.loc[id_energy_carrier]
        taxes_start_year_in_euro_per_gj = taxes['taxes_start_year_in_euro_per_gj']
        taxes_end_year_in_euro_per_gj = taxes['taxes_end_year_in_euro_per_gj']

        minimum_use = self._minimum_use.loc[id_energy_carrier]
        minimum_use_start_year_in_gj = minimum_use['minimum_use_start_year_in_gj']
        minimum_use_end_year_in_gj = minimum_use['minimum_use_end_year_in_gj']

        purchase_price_in_euro_per_gj = self._purchase_price.loc[id_energy_carrier]

        sell_price_in_euro_per_gj = self._sell_price.loc[id_energy_carrier]

        maximum_production_in_gj = self._maximum_production['maximum_production_in_gj'][id_energy_carrier]

        data = {
            'direct_emission_in_t_co2_per_gj': direct_emission_in_t_per_gj,
            'upstream_emission_start_year_in_t_co2_per_gj': upstream_emission_start_year_in_t_co2_per_gj,
            'upstream_emission_end_year_in_t_co2_per_gj': upstream_emission_end_year_in_t_co2_per_gj,
            'renewably_bound_co2_emission_in_t_co2_per_gj': renewably_bound_co2_emission_in_t_co2_per_gj,
            'minimum_use_start_year_in_gj': minimum_use_start_year_in_gj,
            'minimum_use_end_year_in_gj': minimum_use_end_year_in_gj,
            'purchase_price_in_euro_per_gj': purchase_price_in_euro_per_gj,
            'sell_price_in_euro_per_gj': sell_price_in_euro_per_gj,
            'subsidies_start_year_in_euro_per_gj': subsidies_start_year_in_euro_per_gj,
            'subsidies_interim_year_in_euro_per_gj': subsidies_interim_year_in_euro_per_gj,
            'subsidies_end_year_in_euro_per_gj': subsidies_end_year_in_euro_per_gj,
            'taxes_start_year_in_euro_per_gj': taxes_start_year_in_euro_per_gj,
            'taxes_end_year_in_euro_per_gj': taxes_end_year_in_euro_per_gj,
            'maximum_production_in_gj': maximum_production_in_gj,
        }

        energy_carrier = EnergyCarrier(id_energy_carrier, name, data)
        return energy_carrier
