# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from by_product.by_product import ByProduct
from energy_carrier.energy_carrier import EnergyCarrier
from product.product import Product
from result.visitor.visitor import Visitor


class IndexingVisitor(Visitor):
    # Serves as a base class for visitors that
    # remember the visited objects and their indices until
    # the next objects of the same type are visited.

    def __init__(self, simulation_options):
        self._simulation_options = simulation_options

        self._region_indices = [
            'id_scenario',
            'id_region',
        ]

        self._site_indices = [
            *self._region_indices,
            'id_site',
        ]

        self._production_unit_indices = [
            *self._site_indices,
            'id_production_unit',
        ]

        self._base_indices = [
            *self._production_unit_indices,
            'id_sub_production_unit',
            'id_process',
        ]

        self._id_scenario = None

        self._region = None
        self._id_region = None

        self._site = None
        self._id_site = None

        self._production_unit = None
        self._id_production_unit = None
        self._id_sector = None

        self._sub_production_unit = None
        self._id_sub_production_unit = None

        self._process = None
        self._id_process = None

        self._energy_carrier = None
        self._id_energy_carrier = None

        self._product = None
        self._id_product = None

        self._by_product = None
        self._id_by_product = None

    def enter_region(self, region, year):
        logging.debug('Entering region %s in %s', region.id, year)
        self._region = region
        self._id_scenario = region.id_scenario
        self._id_region = region.id

    def enter_site(self, site, year):
        logging.debug('Entering site %s in %s', site.id, year)
        self._site = site
        self._id_site = site.id

    def enter_production_unit(self, production_unit, year):
        logging.debug('Entering production unit %s in %s', production_unit.id, year)
        self._production_unit = production_unit
        self._id_production_unit = production_unit.id

        sector = production_unit.sector
        self._id_sector = sector.id

    def enter_sub_production_unit(self, sub_production_unit, year):
        logging.debug('Entering sub production unit %s in %s', sub_production_unit.id, year)
        self._sub_production_unit = sub_production_unit
        self._id_sub_production_unit = sub_production_unit.id

    def enter_process(self, process, year):
        logging.debug('Entering processes %s in %s', process.id, year)
        self._process = process
        self._id_process = process.id

    def enter_output(self, output, year):
        logging.debug('Entering output %s in %s', output, year)
        carrier = output.carrier
        if isinstance(carrier, Product):
            self._product = carrier
            self._id_product = carrier.id
            self._id_by_product = None
            self._by_product = None
            self._id_energy_carrier = None
            self._energy_carrier = None
        elif isinstance(carrier, ByProduct):
            self._by_product = carrier
            self._id_by_product = carrier.id
            self._id_product = None
            self._product = None
            self._id_energy_carrier = None
            self._energy_carrier = None
        elif isinstance(carrier, EnergyCarrier):
            self._energy_carrier = carrier
            self._id_energy_carrier = carrier.id
            self._id_product = None
            self._product = None
            self._id_by_product = None
            self._by_product = None
        else:
            message = f'Unknown carrier type {type(carrier)}'
            raise TypeError(message)

    def finalize(self):
        pass
