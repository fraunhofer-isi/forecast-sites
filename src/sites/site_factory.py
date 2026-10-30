# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from production_unit.production_unit_factory import ProductionUnitFactory
from sites.site import Site
from sub_production_unit.sub_production_unit_factory import SubProductionUnitFactory


class SiteFactory:
    def __init__(
        self,
        data_interface,
        sector_map,
        process_map,
        energy_carrier_map,
        product_map,
        by_product_map,
        optimization_factory,
        simulation_options,
    ):
        self._site_data = data_interface.site_data
        self._id_region = data_interface.id_region
        self._process_map = process_map
        self._carriers = self._merge_carriers(
            energy_carrier_map,
            product_map,
            by_product_map,
        )

        sub_production_unit_factory = SubProductionUnitFactory(data_interface, process_map)

        self._production_unit_factory = ProductionUnitFactory(
            data_interface,
            sub_production_unit_factory,
            sector_map,
            process_map,
            self._carriers,
            product_map,
            optimization_factory,
            simulation_options,
        )

    @staticmethod
    def _merge_carriers(
        energy_carrier_dictionary,
        products_dictionary,
        by_products_dictionary,
    ):
        energy_carriers = list(energy_carrier_dictionary.values())
        products = list(products_dictionary.values())
        by_products = list(by_products_dictionary.values())
        carriers = energy_carriers + products + by_products
        return carriers

    def create_sites(self, region):
        if len(self._site_data) == 0:
            message = f'No sites found for region {region.id}.'
            raise ValueError(message)

        sites = list(
            self._site_data.apply(
                self._create_site,
                args=(region,),
                axis=1,
            )
        )
        return sites

    def _create_site(
        self,
        row,
        region,
    ):
        id_site = row.name
        geometry = row['geometry']

        site = Site(
            id_site,
            region,
            geometry,
            self._process_map,
        )

        production_units = self._production_unit_factory.create(site)
        site.production_units = production_units
        return site
