# © 2024-2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

class FeedstockDemand:
    def __init__(self, energy_carrier, feedstock_demand_in_gj_per_ton):
        self.energy_carrier = energy_carrier
        self.feedstock_demand_in_gj_per_ton = feedstock_demand_in_gj_per_ton

    def feedstock_cost_in_euro_per_ton(self, year):
        return self.feedstock_demand_in_gj_per_ton * self.energy_carrier.cost_in_euro_per_gj(year)

    def feedstock_emission_in_ton_co2_per_ton(self, year):
        return self.feedstock_demand_in_gj_per_ton * self.energy_carrier.emission_in_ton_per_gj(year)

    def feedstock_subsidies_in_euro_per_ton(self, year):
        return self.feedstock_demand_in_gj_per_ton * self.energy_carrier.subsidies_in_euro_per_gj(year)

    def feedstock_taxes_in_euro_per_ton(self, year):
        return self.feedstock_demand_in_gj_per_ton * self.energy_carrier.taxes_in_euro_per_gj(year)

    def get_energy_carrier_id(self):
        return self.energy_carrier.id
