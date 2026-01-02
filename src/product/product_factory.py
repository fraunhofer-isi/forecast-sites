# © 2024-2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from product.product import Product


class ProductFactory:
    def __init__(self, data_interface, process_factory):
        self._product_process_mapping = data_interface.product_process_mapping
        self._process_factory = process_factory

    def create_product(self, id_product):
        process_entries = self._product_process_mapping.loc[id_product]
        alternative_process_entries = process_entries[process_entries['is_alternative_process'] == 1]
        process_ids = list(alternative_process_entries.index)
        available_processes = self._process_factory.create_processes(id_product, process_ids)

        product = Product(id_product, available_processes)
        return product
