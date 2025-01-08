# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from energy_carrier.energy_carrier import EnergyCarrier


class EnergyCarrierFactory:

    def __init__(self, data_interface):
        self._id_scenario = data_interface.id_scenario
        self._id_region = data_interface.id_region
        self._energy_carrier_data = data_interface.energy_carrier_data
        self._energy_carrier_cost_mapping = data_interface.energy_carrier_cost_mapping
        self._energy_carrier_emission_mapping = data_interface.energy_carrier_emission_mapping
        self._region_energy_carrier_availability_mapping = data_interface.region_energy_carrier_availability_mapping
        self._region_energy_carrier_subsidies_mapping = data_interface.region_energy_carrier_subsidies
        self._region_energy_carrier_taxes_mapping = data_interface.region_energy_carrier_taxes

    def create_energy_carrier_map(self):
        energy_carrier_map = {}
        for _, row in self._energy_carrier_data.iterrows():
            id_energy_carrier = row['id']
            name = row['name']
            energy_carrier_map[id_energy_carrier] = self._create_energy_carrier(id_energy_carrier, name)
        return energy_carrier_map

    def _create_energy_carrier(self, id_energy_carrier, name):
        row_cost = self._energy_carrier_cost_mapping.loc[self._id_scenario, self._id_region, id_energy_carrier]

        row_emission = self._energy_carrier_emission_mapping.loc[self._id_scenario, self._id_region, id_energy_carrier]

        row_availability = self._region_energy_carrier_availability_mapping.loc[
            self._id_scenario,
            self._id_region,
            id_energy_carrier,
        ]

        row_subsidies = self._region_energy_carrier_subsidies_mapping.loc[
            self._id_scenario,
            self._id_region,
            id_energy_carrier,
        ]

        row_taxes = self._region_energy_carrier_taxes_mapping.loc[self._id_scenario, self._id_region, id_energy_carrier]

        cost_2015_in_euro_per_gj = row_cost['cost_2015_in_euro_per_gj']
        cost_2030_in_euro_per_gj = row_cost['cost_2030_in_euro_per_gj']
        cost_2050_in_euro_per_gj = row_cost['cost_2050_in_euro_per_gj']

        emission_2015_in_ton_per_gj = row_emission['emission_2015_in_ton_per_gj']
        emission_2050_in_ton_per_gj = row_emission['emission_2050_in_ton_per_gj']

        availability_2015_in_gj = row_availability['availability_2015_in_gj']
        availability_2050_in_gj = row_availability['availability_2050_in_gj']

        subsidies_2015_in_euro_per_gj = row_subsidies['subsidies_2015_in_euro_per_gj']
        subsidies_2030_in_euro_per_gj = row_subsidies['subsidies_2030_in_euro_per_gj']
        subsidies_2050_in_euro_per_gj = row_subsidies['subsidies_2050_in_euro_per_gj']

        taxes_2015_in_euro_per_gj = row_taxes['taxes_2015_in_euro_per_gj']
        taxes_2050_in_euro_per_gj = row_taxes['taxes_2050_in_euro_per_gj']

        data = {
            'cost_2015_in_euro_per_gj': cost_2015_in_euro_per_gj,
            'cost_2030_in_euro_per_gj': cost_2030_in_euro_per_gj,
            'cost_2050_in_euro_per_gj': cost_2050_in_euro_per_gj,
            'emission_2015_in_ton_per_gj': emission_2015_in_ton_per_gj,
            'emission_2050_in_ton_per_gj': emission_2050_in_ton_per_gj,
            'availability_2015_in_gj': availability_2015_in_gj,
            'availability_2050_in_gj': availability_2050_in_gj,
            'subsidies_2015_in_euro_per_gj': subsidies_2015_in_euro_per_gj,
            'subsidies_2030_in_euro_per_gj': subsidies_2030_in_euro_per_gj,
            'subsidies_2050_in_euro_per_gj': subsidies_2050_in_euro_per_gj,
            'taxes_2015_in_euro_per_gj': taxes_2015_in_euro_per_gj,
            'taxes_2050_in_euro_per_gj': taxes_2050_in_euro_per_gj,
        }

        energy_carrier = EnergyCarrier(id_energy_carrier, name, data)
        return energy_carrier
