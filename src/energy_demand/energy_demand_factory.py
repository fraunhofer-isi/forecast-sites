# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from energy_demand.energy_demand import EnergyDemand


class EnergyDemandFactory:

    def __init__(self, data_interface, energy_carriers):
        self._process_energy_carrier_mapping = data_interface.process_energy_carrier_mapping
        self._energy_carriers = energy_carriers

        id_electricity = 1
        self.electricity = self._energy_carriers[id_electricity]

    def create_energy_demands(
        self,
        id_product,
        id_process,
        electricity_demand_in_gj_per_ton,
        fuel_demand_in_gj_per_ton,
    ):
        energy_demands = [EnergyDemand(self.electricity, electricity_demand_in_gj_per_ton)]

        if fuel_demand_in_gj_per_ton > 0:
            try:
                query = 'id_product==' + str(id_product) + '&id_process==' + str(id_process)
                fuel_share_entries = self._process_energy_carrier_mapping.query(query)
            except KeyError as error:
                message = (
                    'No feedstock shares for id_product | id_process: ' + str(id_product) + ' | ' + str(id_process)
                )
                raise Exception(message) from error

            for _, row in fuel_share_entries.iterrows():
                energy_demand = self._create_energy_demand(row, fuel_demand_in_gj_per_ton)
                energy_demands.append(energy_demand)

        return energy_demands

    def _create_energy_demand(self, row, fuel_demand_in_gj_per_ton):
        id_energy_carrier = row['id_energy_carrier']
        energy_carrier = self._energy_carriers[id_energy_carrier]

        fuel_share = row['fuel_share']
        demand_in_gj_per_ton = fuel_demand_in_gj_per_ton * fuel_share

        energy_demand = EnergyDemand(energy_carrier, demand_in_gj_per_ton)
        return energy_demand
