# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from data_interface import DataInterface
from region.region import Region


class RegionFactory:
    def __init__(self, id_scenario, scenario_options):
        self._id_scenario = id_scenario
        self._scenario_options = scenario_options

    def create_regions(self):
        region_ids = self._scenario_options['region_ids']
        regions = {}
        for region_id in region_ids:
            region = self._create_region(region_id)
            regions[region_id] = region
        return regions

    def _create_region(self, region_id):
        data_interface = DataInterface(
            self._id_scenario,
            self._scenario_options,
            region_id,
        )
        region = Region(region_id, data_interface)
        return region
