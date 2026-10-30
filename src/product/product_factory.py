# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from product.product import Product


class ProductFactory:
    def __init__(
        self,
        data_interface,
    ):
        self._product_data = data_interface.product_data
        self._purchase_price = data_interface.product_purchase_price
        self._sell_price = data_interface.product_sell_price
        self._emission = data_interface.product_emission
        self._maximum_production = data_interface.product_maximum_production

    def create_map(self):
        product_map = {}
        for _, row in self._product_data.iterrows():
            id_product = row['id']
            name = row['name']
            product = self._product(id_product, name)
            product_map[id_product] = product

        return product_map

    def _product(self, id_product, name):
        purchase_price_in_euro_per_t = self._purchase_price.loc[id_product]

        sell_price_in_euro_per_t = self._sell_price.loc[id_product]

        emission = self._emission.loc[id_product]

        upstream_emission_start_year_in_t_co2_per_t = emission['upstream_emission_start_year_in_t_co2_per_t']
        upstream_emission_end_year_in_t_co2_per_t = emission['upstream_emission_end_year_in_t_co2_per_t']
        downstream_emission_in_t_co2_per_t = emission['downstream_emission_in_t_co2_per_t']

        maximum_production_in_t = self._maximum_production['maximum_production_in_t'][id_product]

        data = {
            'purchase_price_in_euro_per_t': purchase_price_in_euro_per_t,
            'sell_price_in_euro_per_t': sell_price_in_euro_per_t,
            'upstream_emission_start_year_in_t_co2_per_t': upstream_emission_start_year_in_t_co2_per_t,
            'upstream_emission_end_year_in_t_co2_per_t': upstream_emission_end_year_in_t_co2_per_t,
            'downstream_emission_in_t_co2_per_t': downstream_emission_in_t_co2_per_t,
            'maximum_production_in_t': maximum_production_in_t,
        }

        product = Product(id_product, name, data)
        return product
