# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later


class SteamDemand:
    def __init__(self, energy_carrier, steam_demand_in_gj_per_ton):
        self.energy_carrier = energy_carrier
        self.steam_demand_in_gj_per_ton = steam_demand_in_gj_per_ton

    def steam_cost_in_euro_per_ton(self, year):
        return self.steam_demand_in_gj_per_ton * self.energy_carrier.cost_in_euro_per_gj(year)

    def steam_emission_in_ton_co2_per_ton(self, year):
        return self.steam_demand_in_gj_per_ton * self.energy_carrier.emission_in_ton_per_gj(year)

    def steam_subsidies_in_euro_per_ton(self, year):
        return self.steam_demand_in_gj_per_ton * self.energy_carrier.subsidies_in_euro_per_gj(year)

    def steam_taxes_in_euro_per_ton(self, year):
        return self.steam_demand_in_gj_per_ton * self.energy_carrier.taxes_in_euro_per_gj(year)

    def get_energy_carrier_id(self):
        return self.energy_carrier.id
