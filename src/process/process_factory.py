# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from energy_demand.energy_demand_factory import EnergyDemandFactory
from feedstock_demand.feedstock_demand_factory import FeedstockDemandFactory
from process.process import Process
from steam_demand.steam_demand_factory import SteamDemandFactory


class ProcessFactory:

    def __init__(self, data_interface, energy_carriers):
        self._product_process_mapping = data_interface.product_process_mapping
        self._process_energy_carrier_mapping = data_interface.process_energy_carrier_mapping
        self._energy_demand_factory = EnergyDemandFactory(data_interface, energy_carriers)
        self._feedstock_demand_factory = FeedstockDemandFactory(data_interface, energy_carriers)
        self._steam_demand_factory = SteamDemandFactory(data_interface, energy_carriers)

    def create_processes(self, id_product, process_ids):
        processes = list(map(lambda id_process: self.create_process(id_product, id_process), process_ids))
        return processes

    # pylint: disable=too-many-locals
    def create_process(self, id_product, id_process):
        process_entry = self._product_process_mapping.loc[id_product, id_process]
        capex_2015_in_euro_per_ton = process_entry['capex_2015_in_euro_per_ton']
        capex_2050_in_euro_per_ton = process_entry['capex_2050_in_euro_per_ton']

        opex_2015_in_euro_per_ton = process_entry['opex_2015_in_euro_per_ton']
        opex_2050_in_euro_per_ton = process_entry['opex_2050_in_euro_per_ton']

        lifetime_in_years = process_entry['lifetime_in_years']
        interest_rate = process_entry['interest_rate']
        depreciation_period = process_entry['depreciation_period']
        process_emission_in_ton_co2_per_ton = process_entry['process_emission_in_ton_co2_per_ton']

        efficiency_improvement_2015 = process_entry['efficiency_improvement_2015']
        efficiency_improvement_2050 = process_entry['efficiency_improvement_2050']

        investment_funding_2015 = process_entry['investment_funding_2015']
        investment_funding_2050 = process_entry['investment_funding_2050']

        investment_flexibility_2015 = process_entry['investment_flexibility_2015']
        investment_flexibility_2050 = process_entry['investment_flexibility_2050']

        electricity_demand_in_gj_per_ton = process_entry['electricity_demand_in_gj_per_ton']
        fuel_demand_in_gj_per_ton = process_entry['fuel_demand_in_gj_per_ton']

        feedstock_demand_in_gj_per_ton = process_entry['feedstock_demand_in_gj_per_ton']
        steam_demand_in_gj_per_ton = process_entry['steam_demand_in_gj_per_ton']

        energy_demands = self._energy_demand_factory.create_energy_demands(
            id_product,
            id_process,
            electricity_demand_in_gj_per_ton,
            fuel_demand_in_gj_per_ton,
        )

        feedstock_demands = self._feedstock_demand_factory.create_feedstock_demands(
            id_product,
            id_process,
            feedstock_demand_in_gj_per_ton,
        )

        steam_demands = self._steam_demand_factory.create_steam_demands(
            id_product,
            id_process,
            steam_demand_in_gj_per_ton,
        )

        process = Process(
            id_process,
            capex_2015_in_euro_per_ton,
            capex_2050_in_euro_per_ton,
            opex_2015_in_euro_per_ton,
            opex_2050_in_euro_per_ton,
            lifetime_in_years,
            interest_rate,
            depreciation_period,
            process_emission_in_ton_co2_per_ton,
            efficiency_improvement_2015,
            efficiency_improvement_2050,
            investment_funding_2015,
            investment_funding_2050,
            investment_flexibility_2015,
            investment_flexibility_2050,
            energy_demands,
            feedstock_demands,
            steam_demands,
        )
        return process
