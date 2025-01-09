# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from energy_carrier.energy_carrier_factory import EnergyCarrierFactory
from entity import Entity
from industrial_site.site_factory import SiteFactory


class Region(Entity):

    def __init__(self, id_region, data_interface):
        self.id = id_region
        self._data_interface = data_interface

        energy_carrier_factory = EnergyCarrierFactory(self._data_interface)
        self._energy_carriers = energy_carrier_factory.create_energy_carrier_map()

        site_factory = SiteFactory(self._data_interface, self._energy_carriers)
        self.sites = site_factory.create_sites()

    def co2_cost_in_euro_per_ton_c02(self, year):
        return self._data_interface.co2_cost_in_euro_per_ton_co2(year)

    def process_year(self, year, simulation_mode, pipeline_cost_scaling, distance_to_closest_h2_pipeline):
        co2_cost_in_euro_per_ton_co2 = self.co2_cost_in_euro_per_ton_c02(year)

        if pipeline_cost_scaling == 0:
            pipeline_cost_scaling = 1000000000
        for site in self.sites:
            distance = distance_to_closest_h2_pipeline
            site.process_year(year, simulation_mode, co2_cost_in_euro_per_ton_co2, pipeline_cost_scaling, distance)

    def site_df(self):
        site_df = self._data_interface.site_data.copy(deep=True)
        shorter_column_names = {
            'id_company': 'id_comp',
            'co2_equivalent_2015_in_tons': 'co2_equ',
        }
        site_df = site_df.rename(columns=shorter_column_names)
        return site_df

    def accept(self, visitor, year):
        visitor.visit_region(self, year)
        for site in self.sites:
            site.accept(visitor, year)

    def get_process_ids_for_site(self, id_site):
        site = next(filter(lambda current_site: current_site.id == id_site, self.sites))
        process_ids = []
        for production_unit in site.production_units:
            id_process = production_unit.process.id
            process_ids.append(id_process)
        return process_ids

    @property
    def scenario(self):
        return self._data_interface.id_scenario
