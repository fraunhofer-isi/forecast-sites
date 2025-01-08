# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from utils.time_utils import exponential_decrease, interpolate, interpolate_cost


class EnergyCarrier:

    def __init__(self, id_energy_carrier, name, data):
        self.id = id_energy_carrier
        self._name = name
        self._cost_2015_in_euro_per_gj = data['cost_2015_in_euro_per_gj']
        self._cost_2030_in_euro_per_gj = data['cost_2030_in_euro_per_gj']
        self._cost_2050_in_euro_per_gj = data['cost_2050_in_euro_per_gj']
        self._emission_2015_in_ton_per_gj = data['emission_2015_in_ton_per_gj']
        self._emission_2050_in_ton_per_gj = data['emission_2050_in_ton_per_gj']
        self._availability_2015_in_gj = data['availability_2015_in_gj']
        self._availability_2050_in_gj = data['availability_2050_in_gj']
        self._subsidies_2015_in_euro_per_gj = data['subsidies_2015_in_euro_per_gj']
        self._subsidies_2030_in_euro_per_gj = data['subsidies_2030_in_euro_per_gj']
        self._subsidies_2050_in_euro_per_gj = data['subsidies_2050_in_euro_per_gj']
        self._taxes_2015_in_euro_per_gj = data['taxes_2015_in_euro_per_gj']
        self._taxes_2050_in_euro_per_gj = data['taxes_2050_in_euro_per_gj']

    def cost_in_euro_per_gj(self, year):
        return exponential_decrease(
            year,
            self._cost_2015_in_euro_per_gj,
            self._cost_2030_in_euro_per_gj,
            self._cost_2050_in_euro_per_gj,
        )

    def emission_in_ton_per_gj(self, year):
        return interpolate(year, self._emission_2015_in_ton_per_gj, self._emission_2050_in_ton_per_gj)

    def availability_in_gj(self, year):
        return interpolate(year, self._availability_2015_in_gj, self._availability_2050_in_gj)

    def subsidies_in_euro_per_gj(self, year):
        return interpolate_cost(
            year,
            self._subsidies_2015_in_euro_per_gj,
            self._subsidies_2030_in_euro_per_gj,
            self._subsidies_2050_in_euro_per_gj,
        )

    def taxes_in_euro_per_gj(self, year):
        return interpolate(year, self._taxes_2015_in_euro_per_gj, self._taxes_2050_in_euro_per_gj)
