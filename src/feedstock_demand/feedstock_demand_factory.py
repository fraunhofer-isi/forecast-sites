# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from feedstock_demand.feedstock_demand import FeedstockDemand


class FeedstockDemandFactory:

    def __init__(self, data_interface, energy_carriers):
        self._process_feedstock_mapping = data_interface.process_feedstock_mapping
        self._energy_carriers = energy_carriers

    def create_feedstock_demands(
        self,
        id_product,
        id_process,
        feedstock_demand_in_gj_per_ton,
    ):

        feedstock_demands = []

        if feedstock_demand_in_gj_per_ton > 0:
            try:
                query = 'id_product==' + str(id_product) + '&id_process==' + str(id_process)
                feedstock_share_entries = self._process_feedstock_mapping.query(query)
            except KeyError as error:
                message = 'No fuel shares for id_product | id_process: ' + str(id_product) + ' | ' + str(id_process)
                raise Exception(message) from error

            for _, row in feedstock_share_entries.iterrows():
                feedstock_demand = self._create_feedstock_demand(row, feedstock_demand_in_gj_per_ton)
                feedstock_demands.append(feedstock_demand)
        return feedstock_demands

    def _create_feedstock_demand(self, row, feedstock_demand_in_gj_per_ton):
        id_energy_carrier = row['id_energy_carrier']
        energy_carrier = self._energy_carriers[id_energy_carrier]

        feedstock_share = row['feedstock_share']
        feed_demand_in_gj_per_ton = feedstock_demand_in_gj_per_ton * feedstock_share

        feedstock_demand = FeedstockDemand(energy_carrier, feed_demand_in_gj_per_ton)
        return feedstock_demand
