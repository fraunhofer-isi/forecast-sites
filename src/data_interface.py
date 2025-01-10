# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import sqlite3

import geopandas
import pandas as pd

from utils import collection_utils, time_utils


# pylint: disable=too-many-instance-attributes
class DataInterface:
    def __init__(self, id_scenario, scenario_options, id_region):
        self.id_scenario = id_scenario
        self._scenario_options = scenario_options
        self.id_region = id_region

        connection = sqlite3.connect('./input/input.sqlite')
        with connection:
            self.energy_carrier_data = self._read_energy_carrier_data(connection)

            id_product_filter = self._scenario_options['id_product_filter']
            self.site_data = self._read_site_data(connection)
            site_ids = self._get_site_ids()

            self.production_unit_mapping = self._read_production_unit_mapping_and_delete_unused_sites(
                site_ids, connection, id_product_filter
            )

            self.product_process_mapping = self._read_product_process_mapping(connection, id_product_filter)

            self.process_energy_carrier_mapping = self._read_process_energy_carrier_mapping(
                connection, id_product_filter
            )

            self.process_steam_mapping = self._read_process_steam_mapping(connection, id_product_filter)

            self.process_feedstock_mapping = self._read_process_feedstock_mapping(connection, id_product_filter)

            self.energy_carrier_cost_mapping = self._read_energy_carrier_cost_mapping(connection)
            self.energy_carrier_emission_mapping = self._read_energy_carrier_emission_mapping(connection)
            self.region_energy_carrier_availability_mapping = self._read_region_energy_carrier_availability_mapping(
                connection
            )
            self.region_energy_carrier_subsidies = self._read_region_energy_carrier_subsidies(connection)
            self.region_energy_carrier_taxes = self._read_region_energy_carrier_taxes(connection)

    def co2_cost_in_euro_per_ton_co2(self, year):
        return time_utils.interpolate(
            year,
            self._scenario_options['co2_cost_2015_in_euro_per_ton_co2'],
            self._scenario_options['co2_cost_2050_in_euro_per_ton_co2'],
        )

    @staticmethod
    def _read_energy_carrier_data(connection):
        query = 'SELECT * from id_energy_carrier'
        df = pd.read_sql_query(query, connection)
        return df

    def _read_site_data(self, connection):
        query = 'SELECT * from site WHERE id_region = ?'
        df = pd.read_sql_query(query, connection, index_col=['id'], params=(self.id_region,))

        df['geometry'] = geopandas.points_from_xy(df['longitude'], df['latitude'])
        geo_df = geopandas.GeoDataFrame(df, geometry='geometry')

        return geo_df

    def _get_site_ids(self):
        return list(self.site_data.apply(lambda row: row.name, axis=1))

    def _read_production_unit_mapping_and_delete_unused_sites(self, site_ids, connection, id_product_filter):
        is_filtering_products = len(id_product_filter) > 0
        product_ids = collection_utils.join_with_comma(id_product_filter)

        site_map = {}
        for id_site in site_ids:
            query = 'SELECT * from production_unit WHERE id_site = ?'

            if is_filtering_products:
                query += ' AND id_product IN (' + product_ids + ')'

            df = pd.read_sql_query(query, connection, params=(id_site,))
            if len(df) > 0:
                site_map[id_site] = df
            else:
                self.site_data = self.site_data.drop(id_site)

        return site_map

    @staticmethod
    def _read_product_process_mapping(connection, id_product_filter):
        is_filtering_products = len(id_product_filter) > 0
        product_ids = collection_utils.join_with_comma(id_product_filter)

        query = 'SELECT * from product_process_mapping_jrc'
        if is_filtering_products:
            query += ' WHERE id_product IN (' + product_ids + ')'

        df = pd.read_sql_query(query, connection, index_col=['id_product', 'id_process'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_process_energy_carrier_mapping(connection, id_product_filter):
        is_filtering_products = len(id_product_filter) > 0
        product_ids = collection_utils.join_with_comma(id_product_filter)

        query = 'SELECT * from process_energy_carrier_mapping_jrc'
        if is_filtering_products:
            query += ' WHERE id_product IN (' + product_ids + ')'

        df = pd.read_sql_query(query, connection, index_col=['id_product', 'id_process'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_process_feedstock_mapping(connection, id_product_filter):
        is_filtering_products = len(id_product_filter) > 0
        product_ids = collection_utils.join_with_comma(id_product_filter)

        query = 'SELECT * from process_feedstock_mapping_jrc'
        if is_filtering_products:
            query += ' WHERE id_product IN (' + product_ids + ')'

        df = pd.read_sql_query(query, connection, index_col=['id_product', 'id_process'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_process_steam_mapping(connection, id_product_filter):
        is_filtering_products = len(id_product_filter) > 0
        product_ids = collection_utils.join_with_comma(id_product_filter)

        query = 'SELECT * from process_steam_mapping_jrc'
        if is_filtering_products:
            query += ' WHERE id_product IN (' + product_ids + ')'

        df = pd.read_sql_query(query, connection, index_col=['id_product', 'id_process'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_energy_carrier_cost_mapping(connection):
        query = 'SELECT * from energy_carrier_cost'
        df = pd.read_sql_query(query, connection, index_col=['id_scenario', 'id_region', 'id_energy_carrier'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_energy_carrier_emission_mapping(connection):
        query = 'SELECT * from energy_carrier_emission'
        df = pd.read_sql_query(query, connection, index_col=['id_scenario', 'id_region', 'id_energy_carrier'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_region_energy_carrier_availability_mapping(connection):
        query = 'SELECT * from region_energy_carrier_availability_mapping'
        df = pd.read_sql_query(query, connection, index_col=['id_scenario', 'id_region', 'id_energy_carrier'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_region_energy_carrier_subsidies(connection):
        query = 'SELECT * from energy_carrier_subsidies'
        df = pd.read_sql_query(query, connection, index_col=['id_scenario', 'id_region', 'id_energy_carrier'])
        df = df.sort_index()
        return df

    @staticmethod
    def _read_region_energy_carrier_taxes(connection):
        query = 'SELECT * from energy_carrier_taxes'
        df = pd.read_sql_query(query, connection, index_col=['id_scenario', 'id_region', 'id_energy_carrier'])
        df = df.sort_index()
        return df
