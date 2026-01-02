# © 2024-2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from industrial_site.site import Site
from production_unit.production_unit_factory import ProductionUnitFactory


class SiteFactory:
    def __init__(self, data_interface, energy_carriers):
        self._site_data = data_interface.site_data
        self._region_id = data_interface.id_region
        self._production_unit_factory = ProductionUnitFactory(data_interface, energy_carriers)

    def create_sites(self):
        if len(self._site_data) < 1:
            return []
        sites = list(self._site_data.apply(self._create_site, axis=1))
        return sites

    def _create_site(self, row):
        id_site = row.name
        geometry = row['geometry']
        production_units = self._production_unit_factory.create_production_units(id_site)

        return Site(
            id_site,
            geometry,
            production_units,
        )
