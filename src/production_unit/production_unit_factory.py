# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from interpolation.interpolation_data import InterpolationData
from production_unit.production_unit import ProductionUnit


class ProductionUnitFactory:
    def __init__(
        self,
        data_interface,
        sub_production_unit_factory,
        sector_map,
        process_map,
        carriers,
        product_map,
        optimization_factory,
        simulation_options,
    ):
        self._data_interface = data_interface
        self._site_production_unit_mapping = data_interface.site_production_unit_mapping

        self._sub_production_unit_factory = sub_production_unit_factory
        self._sector_map = sector_map
        self._process_map = process_map
        self._carriers = carriers
        self._product_map = product_map
        self._optimization_factory = optimization_factory
        self._simulation_options = simulation_options

    def create(self, site):
        id_site = site.id
        production_unit_df = self._site_production_unit_mapping[id_site]
        if len(production_unit_df) == 0:
            message = f'No production units found for site {id_site}.'
            raise ValueError(message)

        production_units = []
        for _, row in production_unit_df.iterrows():
            production_unit = self._create_production_unit(site, row)
            production_units.append(production_unit)
        return production_units

    def _create_production_unit(self, site, row):
        id_production_unit = int(row.name)
        minimum_export_interpolation_data_in_t = self._minimum_export_interpolation_data_in_t(id_production_unit)

        id_sector = int(row['id_sector'])
        sector = self._sector_map[id_sector]
        process_map_for_sector = self._filter_process_map_for_sector(id_sector)

        production_unit = ProductionUnit(
            id_production_unit,
            site,
            sector,
            minimum_export_interpolation_data_in_t,
            self._sub_production_unit_factory,
            self._optimization_factory,
            process_map_for_sector,
            self._carriers,
            self._simulation_options,
        )
        return production_unit

    def _minimum_export_interpolation_data_in_t(self, id_production_unit):
        mapping = self._data_interface.production_unit_product_mapping
        filtered_mapping = mapping[mapping['id_production_unit'] == id_production_unit]

        minimum_export_interpolation_data = {}
        for _, row in filtered_mapping.iterrows():
            id_product = int(row['id_product'])
            product = self._product_map[id_product]

            minimum_export_start_year_in_t = row['minimum_export_start_year_in_t']
            minimum_export_interim_year_in_t = row['minimum_export_interim_year_in_t']
            minimum_export_end_year_in_t = row['minimum_export_end_year_in_t']
            interpolation_data = InterpolationData(
                minimum_export_start_year_in_t,
                minimum_export_end_year_in_t,
                minimum_export_interim_year_in_t,
            )

            minimum_export_interpolation_data[product] = interpolation_data

        return minimum_export_interpolation_data

    def _filter_process_map_for_sector(self, id_sector):
        filtered_process_map = {}
        for id_process, process in self._process_map.items():
            # if there is a sector filter specified, only include a processes for the matching sectors.
            # if no sector filter is specified, include a process for all sectors
            sector_ids = process.sector_ids
            if sector_ids and id_sector not in sector_ids:
                continue
            filtered_process_map[id_process] = process
        return filtered_process_map
