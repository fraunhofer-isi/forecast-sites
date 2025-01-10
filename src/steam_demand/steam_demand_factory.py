# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from steam_demand.steam_demand import SteamDemand


class SteamDemandFactory:
    def __init__(self, data_interface, energy_carriers):
        self._process_steam_mapping = data_interface.process_steam_mapping
        self._energy_carriers = energy_carriers

    def create_steam_demands(
        self,
        id_product,
        id_process,
        steam_demand_in_gj_per_ton,
    ):
        steam_demands = []

        if steam_demand_in_gj_per_ton > 0:
            try:
                query = 'id_product==' + str(id_product) + '&id_process==' + str(id_process)
                steam_share_entries = self._process_steam_mapping.query(query)
            except KeyError as error:
                message = 'No fuel shares for id_product | id_process: ' + str(id_product) + ' | ' + str(id_process)
                raise ValueError(message) from error

            for _, row in steam_share_entries.iterrows():
                steam_demand = self._create_steam_demand(row, steam_demand_in_gj_per_ton)
                steam_demands.append(steam_demand)

        return steam_demands

    def _create_steam_demand(self, row, steam_demand_in_gj_per_ton):
        id_energy_carrier = row['id_energy_carrier']
        energy_carrier = self._energy_carriers[id_energy_carrier]

        steam_share = row['steam_share']
        demand_in_gj_per_ton = steam_demand_in_gj_per_ton * steam_share

        steam_demand = SteamDemand(energy_carrier, demand_in_gj_per_ton)
        return steam_demand
