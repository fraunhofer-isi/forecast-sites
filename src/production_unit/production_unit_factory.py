# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from process.process_factory_jrc import ProcessFactoryJRC
from product.product_factory import ProductFactory
from production_unit.production_unit import ProductionUnit


class ProductionUnitFactory:
    def __init__(self, data_interface, energy_carriers):
        self._data_interface = data_interface
        self._production_unit_mapping = data_interface.production_unit_mapping
        self._process_factory = ProcessFactoryJRC(data_interface, energy_carriers)
        self._product_factory = ProductFactory(data_interface, self._process_factory)

    def create_production_units(self, id_site):
        production_unit_df = self._production_unit_mapping[id_site]
        production_units = []
        for _, row in production_unit_df.iterrows():
            production_unit = self._create_production_unit(row)
            production_units.append(production_unit)
        return production_units

    def _create_production_unit(self, row):
        id_production_unit = int(row['id'])
        id_product = int(row['id_product'])
        id_process = int(row['id_process'])
        production_in_tons = row['production_in_tons']
        year_of_last_reinvestment = row['year_of_last_reinvestment']

        product = self._product_factory.create_product(id_product)
        process = self._process_factory.create_process(id_product, id_process)

        production_unit = ProductionUnit(
            id_production_unit,
            product,
            process,
            production_in_tons,
            year_of_last_reinvestment,
        )
        return production_unit
