# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import logging
import sqlite3

import geopandas
import pandas as pd

from utils import collection_utils


class DataInterface:
    def __init__(
        self,
        id_scenario: int,
        id_region: int,
        simulation_options: dict,
    ) -> None:
        self._id_scenario = id_scenario
        self._id_region = id_region
        self._simulation_options = simulation_options

        id_product_filter = self._simulation_options['id_product_filter']

        self._read_tables_from_database(id_product_filter)

    @property
    def id_scenario(self) -> int:
        """Explicit semantic access to scenario ID"""
        return self._id_scenario

    @id_scenario.setter
    def id_scenario(self, value: int) -> None:
        """Setter for scenario ID"""
        self._id_scenario = value

    @property
    def id_region(self) -> int:
        """Explicit semantic access to region ID"""
        return self._id_region

    @id_region.setter
    def id_region(self, value: int) -> None:
        """Setter for region ID"""
        self._id_region = value

    @property
    def _end_year(self):
        end_year = self._simulation_options['end_year']
        return end_year

    @property
    def interest_rate(self):
        value = self._interest_rate_data['interest_rate'][0]
        if value <= 0:
            msg = 'The interest rate needs to be > 0.'
            raise ValueError(msg)
        return value

    def co2_cost_in_euro_per_t_co2(self, year):
        year_string = str(year)
        co2_cost_series = self._co2_cost.iloc[0]
        if year_string in co2_cost_series.index:
            return float(co2_cost_series[year_string])
        last_year = max(co2_cost_series.index, key=int)
        return float(co2_cost_series[last_year])

    def energy_carrier_availability_series(self, energy_carrier):
        id_energy_carrier = energy_carrier.id
        if id_energy_carrier not in self._energy_carrier_availability.index:
            return None

        availability_series = self._energy_carrier_availability.loc[id_energy_carrier]
        return availability_series

    def product_availability_series(self, product):
        id_product = product.id
        if id_product not in self._product_availability.index:
            return None
        availability_series = self._product_availability.loc[id_product]
        return availability_series

    def by_product_availability_series(self, by_product):
        id_by_product = by_product.id
        if id_by_product not in self._by_product_availability.index:
            return None
        availability_series = self._by_product_availability.loc[id_by_product]
        return availability_series

    def annual_value_series(self, value, first_year):
        year_increment = self._simulation_options.get('year_increment', 1)
        year_range = range(first_year, self._end_year + 1, year_increment)
        series = pd.Series({str(year): value for year in year_range})
        return series

    def _read_tables_from_database(self, id_product_filter):
        database_path = self._simulation_options['database_path']

        connection = self.database_connection(database_path)
        try:
            self._read_region_tables(connection)
            production_unit_ids = self._read_site_tables(connection, id_product_filter)
            self._read_production_unit_tables(
                connection,
                id_product_filter,
                production_unit_ids,
            )

            self._read_sector_tables(connection)

            self._read_process_tables(connection)
            self._read_energy_carrier_tables(connection)
            self._read_product_tables(connection)
            self._read_by_product_tables(connection)
        finally:
            connection.close()

    def _read_region_tables(self, connection):
        self._interest_rate_data = self._filtered_scenario_table(connection, 'region_interest_rate')
        self._co2_cost = self._filtered_scenario_table(connection, 'co2_cost_in_euro_per_t_co2')

    def _read_site_tables(self, connection, id_product_filter):
        self.site_data = self._site_data(connection, id_product_filter)
        site_ids = self._site_ids()
        self.site_production_unit_mapping, production_unit_ids = self._read_production_units_by_sites(connection, site_ids)
        return production_unit_ids

    def _read_production_unit_tables(
        self,
        connection,
        id_product_filter,
        production_unit_ids,
    ):
        self.production_unit_sub_production_unit_mapping = self._read_production_unit_sub_production_unit_mapping(
            connection,
            production_unit_ids,
        )
        self.production_unit_product_mapping = self._read_production_unit_product_mapping(connection, id_product_filter)

    def _read_sector_tables(self, connection):
        self.sector_data = self.id_table(connection, 'id_sector')

    def _read_process_tables(self, connection):
        self.process_data = self.table(connection, 'process')

        self.process_sector_mapping = self.table(connection, 'process_sector_mapping')

        self.process_energy_carrier_energy_demand = self.table(
            connection, 'process_energy_carrier_energy_demand_in_gj_per_process_count'
        )
        self.process_energy_carrier_feedstock_demand = self.table(
            connection,
            'process_energy_carrier_feedstock_demand_in_gj_per_process_count',
        )
        self.process_energy_carrier_output = self.table(connection, 'process_energy_carrier_output_in_gj_per_process_count')

        self.process_product_feedstock_demand = self.table(connection, 'process_product_feedstock_demand_in_t_per_process_count')
        self.process_by_product_feedstock_demand = self.table(
            connection, 'process_by_product_feedstock_demand_in_t_per_process_count'
        )
        self.process_product_output = self.table(connection, 'process_product_output_in_t_per_process_count')
        self.process_by_product_output = self.table(connection, 'process_by_product_output_in_t_per_process_count')

    def _read_energy_carrier_tables(self, connection):
        self.energy_carrier_data = self.id_table(connection, 'id_energy_carrier')

        self.energy_carrier_emission = self._filtered_scenario_table(connection, 'energy_carrier_emission_in_t_co2_per_gj')

        self._energy_carrier_availability = self._filtered_scenario_table(connection, 'energy_carrier_availability_in_gj')

        self.energy_carrier_subsidies = self._filtered_scenario_table(connection, 'energy_carrier_subsidies_in_euro_per_gj')
        self.energy_carrier_taxes = self._filtered_scenario_table(connection, 'energy_carrier_taxes_in_euro_per_gj')
        self.energy_carrier_minimum_use = self._filtered_scenario_table(connection, 'energy_carrier_minimum_use_in_gj')
        self.energy_carrier_purchase_price = self._filtered_scenario_table(
            connection, 'energy_carrier_purchase_price_in_euro_per_gj'
        )
        self.energy_carrier_sell_price = self._filtered_scenario_table(connection, 'energy_carrier_sell_price_in_euro_per_gj')
        self.energy_carrier_maximum_production = self.table(connection, 'energy_carrier_maximum_production_in_gj')

    def _read_product_tables(self, connection):
        self.product_data = self.id_table(connection, 'id_product')
        self.product_purchase_price = self._filtered_scenario_table(connection, 'product_purchase_price_in_euro_per_t')
        self.product_sell_price = self._filtered_scenario_table(connection, 'product_sell_price_in_euro_per_t')
        self.product_emission = self._filtered_scenario_table(connection, 'product_emission_in_t_co2_per_t')

        self._product_availability = self._filtered_scenario_table(connection, 'product_availability_in_t')
        self.product_maximum_production = self.table(connection, 'product_maximum_production_in_t')

    def _read_by_product_tables(self, connection):
        self.by_product_data = self.id_table(connection, 'id_by_product')
        self.by_product_purchase_price = self._filtered_scenario_table(connection, 'by_product_purchase_price_in_euro_per_t')
        self.by_product_sell_price = self._filtered_scenario_table(connection, 'by_product_sell_price_in_euro_per_t')
        self.by_product_emission = self._filtered_scenario_table(connection, 'by_product_emission_in_t_co2_per_t')

        self._by_product_availability = self._filtered_scenario_table(connection, 'by_product_availability_in_t')
        self.by_product_maximum_production = self.table(connection, 'by_product_maximum_production_in_t')

    @staticmethod
    def database_connection(database_path):
        try:
            connection = sqlite3.connect(database_path)
        except sqlite3.Error as error:
            message = (
                'Could not find input *.sqlite file. (Maybe you started main.py not from project '
                " root directory and want to remove '/src' from your working directory path?)"
            )
            raise OSError(message) from error
        return connection

    @staticmethod
    def id_table(connection, table_name):
        query = f'SELECT * from {table_name}'
        df = pd.read_sql_query(query, connection)
        return df

    @staticmethod
    def table(connection, table_name):
        id_column_names = DataInterface._id_column_names(connection, table_name)
        query = f'SELECT * from {table_name}'
        df = pd.read_sql_query(query, connection, index_col=id_column_names)
        df = df.sort_index()
        return df

    @staticmethod
    def _id_column_names(connection, table_name):
        query = f'PRAGMA table_info({table_name})'
        columns_info = pd.read_sql_query(query, connection)
        names = columns_info['name']
        id_column_names = [name for name in names if name.startswith('id_')]
        return id_column_names

    @staticmethod
    def _read_production_units(connection, production_unit_id_filter):
        production_unit_ids = collection_utils.join_with_comma(production_unit_id_filter)
        query = f'SELECT * from production_unit WHERE id_production_unit IN ({production_unit_ids})'
        df = pd.read_sql_query(query, connection, index_col=['id_production_unit'])
        return df

    @staticmethod
    def _read_production_unit_sub_production_unit_mapping(connection, production_unit_id_filter):
        production_unit_ids = collection_utils.join_with_comma(production_unit_id_filter)
        query = f'SELECT * from sub_production_unit WHERE id_production_unit IN ({production_unit_ids})'
        df = pd.read_sql_query(query, connection, index_col=['id_sub_production_unit'])

        mapping = {}
        for id_production_unit in production_unit_id_filter:
            filtered_df = df[df['id_production_unit'] == id_production_unit]
            mapping[id_production_unit] = filtered_df

        return mapping

    @staticmethod
    def _read_production_units_by_sites(
        connection,
        site_ids,
    ):
        site_map = {}
        production_unit_id_set = set()
        for id_site in site_ids:
            query = 'SELECT * from production_unit WHERE id_site = ?'
            df = pd.read_sql_query(query, connection, params=(id_site,), index_col='id_production_unit')
            if len(df) > 0:
                site_map[id_site] = df
                production_unit_id_set.update(df.index)

        all_production_unit_ids = list(production_unit_id_set)
        return site_map, all_production_unit_ids

    @staticmethod
    def _read_production_unit_product_mapping(connection, id_product_filter):
        is_filtering_products = len(id_product_filter) > 0
        product_ids = collection_utils.join_with_comma(id_product_filter)
        query = 'SELECT * from production_unit_product_mapping_in_t'
        if is_filtering_products:
            query += ' WHERE id_product IN (' + product_ids + ')'
        df = pd.read_sql_query(query, connection)

        if len(df) == 0:
            message = 'No production units found'
            if is_filtering_products:
                message += f' for the given product_ids [{product_ids}].'
            raise ValueError(message)

        return df

    @staticmethod
    def _geo_data_frame(df):
        df['geometry'] = geopandas.points_from_xy(df['longitude'], df['latitude'])
        geo_df = geopandas.GeoDataFrame(df, geometry='geometry')
        geo_df = geo_df.set_crs('EPSG:4326')
        return geo_df

    def _filtered_scenario_table(self, connection, table_name):
        df = DataInterface.table(connection, table_name)
        df = self._filter_for_scenario_and_region(df, table_name)
        return df

    def _filter_for_scenario_and_region(self, df, table_name):
        query = f'id_scenario=={self.id_scenario} and id_region == {self.id_region}'
        filtered_df = df.query(query)
        if len(filtered_df) < 1:
            message = f'No data found for scenario {self.id_scenario} and region {self.id_region} in table {table_name}.'
            raise KeyError(message)

        filtered_df = filtered_df.reset_index(level=['id_scenario', 'id_region'], drop=True)

        sorted_df = filtered_df.sort_index()
        return sorted_df

    def _site_data(self, connection, id_product_filter):
        potential_site_ids = self._potential_site_ids(connection, id_product_filter)
        logging.info('Potential sites for product filter %s: %s', id_product_filter, potential_site_ids)

        query = f'SELECT * from site WHERE id_region = ? AND id_site in ({potential_site_ids})'

        df = pd.read_sql_query(
            query,
            connection,
            index_col=['id_site'],
            params=(self.id_region,),
        )

        if df.empty:
            message = f'No sites with production units found for region {self.id_region} and product filter {id_product_filter}.'
            raise ValueError(message)

        geo_df = self._geo_data_frame(df)

        return geo_df

    def _production_units(self, connection, id_product_filter):
        production_unit_product_mapping = self._read_production_unit_product_mapping(connection, id_product_filter)
        production_unit_id_filter = production_unit_product_mapping['id_production_unit'].unique()
        production_units = self._read_production_units(connection, production_unit_id_filter)

        if len(production_units) == 0:
            message = 'No production units found.'
            raise ValueError(message)

        return production_units

    def _potential_site_ids(self, connection, id_product_filter):
        production_units = self._production_units(connection, id_product_filter)
        site_id_filter = production_units['id_site'].unique()
        potential_site_ids = collection_utils.join_with_comma(site_id_filter)
        return potential_site_ids

    def _site_ids(self):
        return list(self.site_data.apply(lambda row: row.name, axis=1))

    def groups_for_region(self, id_region):
        database_path = self._simulation_options['database_path']
        with self.database_connection(database_path) as connection:
            q = 'SELECT id_group, branch, id_region, description FROM "group" WHERE id_region = ?'
            df = pd.read_sql_query(q, connection, params=(id_region,))
        return df.to_dict('records')

    def group_site_memberships(self, id_region):
        database_path = self._simulation_options['database_path']
        with self.database_connection(database_path) as connection:
            q = """
                SELECT gsm.id_group, gsm.id_site
                FROM group_site_mapping gsm
                JOIN "group" g ON g.id_group = gsm.id_group
                WHERE g.id_region = ?
            """
            df = pd.read_sql_query(q, connection, params=(id_region,))
        return df.to_dict('records')
