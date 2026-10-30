# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from by_product.by_product import ByProduct


class ByProductFactory:
    def __init__(
        self,
        data_interface,
    ):
        self._by_product_data = data_interface.by_product_data
        self._purchase_price = data_interface.by_product_purchase_price
        self._sell_price = data_interface.by_product_sell_price
        self._emission = data_interface.by_product_emission
        self._maximum_production = data_interface.by_product_maximum_production

    def create_map(self):
        by_product_map = {}
        for _, row in self._by_product_data.iterrows():
            id_by_product = row['id']
            name = row['name']
            by_product = self._by_product(id_by_product, name)
            by_product_map[id_by_product] = by_product
        return by_product_map

    def _by_product(self, id_by_product, name):
        purchase_price_in_euro_per_t = self._purchase_price.loc[id_by_product]
        sell_price_in_euro_per_t = self._sell_price.loc[id_by_product]

        emission = self._emission.loc[id_by_product]
        upstream_emission_start_year_in_t_co2_per_t = emission['upstream_emission_start_year_in_t_co2_per_t']
        upstream_emission_end_year_in_t_co2_per_t = emission['upstream_emission_end_year_in_t_co2_per_t']
        downstream_emission_in_t_co2_per_t = emission['downstream_emission_in_t_co2_per_t']

        maximum_production_in_t = self._maximum_production['maximum_production_in_t'][id_by_product]

        # By-products have renewably bound emissions of 0 by design
        renewably_bound_co2_emission_in_t_co2_per_t = 0

        data = {
            'purchase_price_in_euro_per_t': purchase_price_in_euro_per_t,
            'sell_price_in_euro_per_t': sell_price_in_euro_per_t,
            'upstream_emission_start_year_in_t_co2_per_t': upstream_emission_start_year_in_t_co2_per_t,
            'upstream_emission_end_year_in_t_co2_per_t': upstream_emission_end_year_in_t_co2_per_t,
            'downstream_emission_in_t_co2_per_t': downstream_emission_in_t_co2_per_t,
            'renewably_bound_co2_emission_in_t_co2_per_t': renewably_bound_co2_emission_in_t_co2_per_t,
            'maximum_production_in_t': maximum_production_in_t,
        }
        by_product = ByProduct(id_by_product, name, data)
        return by_product
