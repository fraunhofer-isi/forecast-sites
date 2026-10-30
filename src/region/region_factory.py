# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from by_product.by_product_factory import ByProductFactory
from data_layer.data_interface import DataInterface
from energy_carrier.energy_carrier_factory import EnergyCarrierFactory
from optimization.optimization_factory import OptimizationFactory
from processes.process_factory import ProcessFactory
from product.product_factory import ProductFactory
from region.region import Region
from sector.sector_factory import SectorFactory
from sites.site_factory import SiteFactory


class RegionFactory:
    def __init__(self, id_scenario, simulation_options):
        self._id_scenario = id_scenario
        self._simulation_options = simulation_options

        optimization_type = simulation_options['optimization_type']
        self._optimization_factory = OptimizationFactory(optimization_type)

    def create_regions(self):
        region_ids = self._simulation_options['region_ids']
        regions = {}
        for id_region in region_ids:
            region = self._create_region(id_region)
            regions[id_region] = region
        return regions

    def _create_region(self, id_region):
        data_interface = DataInterface(
            self._id_scenario,
            id_region,
            self._simulation_options,
        )

        energy_carrier_factory = EnergyCarrierFactory(data_interface)
        energy_carrier_map = energy_carrier_factory.create_map()

        sector_factory = SectorFactory(data_interface)
        sector_map = sector_factory.create_map()

        product_factory = ProductFactory(data_interface)
        product_map = product_factory.create_map()

        by_product_factory = ByProductFactory(data_interface)
        by_product_map = by_product_factory.create_map()

        process_factory = ProcessFactory(
            data_interface,
            energy_carrier_map,
            product_map,
            by_product_map,
            self._simulation_options,
        )
        process_map = process_factory.create_map()

        site_factory = SiteFactory(
            data_interface,
            sector_map,
            process_map,
            energy_carrier_map,
            product_map,
            by_product_map,
            self._optimization_factory,
            self._simulation_options,
        )

        region = Region(
            id_region,
            data_interface,
            energy_carrier_map,
            sector_map,
            product_map,
            by_product_map,
            process_map,
            site_factory,
            self._simulation_options,
        )
        return region
