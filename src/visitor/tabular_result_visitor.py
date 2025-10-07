# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sqlite3

import pandas as pd

from utils import file_utils
from visitor.visitor import Visitor


# pylint: disable=too-many-instance-attributes
class TabularResultVisitor(Visitor):
    def __init__(self):
        # Initialisation of variables for writing results on different aggregation levels
        self._base_column_names = [
            'id_scenario',
            'id_region',
            'id_site',
            'id_production_unit',
            'id_product',
            'id_process',
        ]

        self._initialize_result_tables()

        self._initialize_virtual_cost_tables()

        self._scenario = None
        self._region = None
        self._id_site = None
        self._id_production_unit = None
        self._id_product = None
        self._id_process = None
        self._production_in_tons = None

        self._year_of_last_reinvestment = None
        self._previous_process = None
        self._process = None
        self._new_investment_in_euro = None
        self._production_cost_in_euro_per_ton = None
        self._energy_carrier_cost_in_euro_per_ton = None

    def _initialize_result_tables(self):
        ## Aggregated result tables
        # Demand tables
        self._final_energy_demand_df = self._empty_energy_carrier_table()
        self._final_steam_demand_df = self._empty_energy_carrier_table()
        self._final_feedstock_demand_df = self._empty_energy_carrier_table()
        # Cost tables
        self._production_cost_df = self._empty_base_table()
        self._investment_df = self._empty_base_table()
        self._annuity_on_investment_df = self._empty_base_table()
        self._energy_cost_df = self._empty_energy_carrier_table()
        self._steam_cost_df = self._empty_energy_carrier_table()
        self._feedstock_cost_df = self._empty_energy_carrier_table()
        self._energy_emission_cost_df = self._empty_energy_carrier_table()
        self._steam_emission_cost_df = self._empty_energy_carrier_table()
        self._process_emission_cost_df = self._empty_base_table()
        # Emission tables
        self._process_emission_df = self._empty_base_table()
        self._energy_emission_df = self._empty_energy_carrier_table()
        self._steam_emission_df = self._empty_energy_carrier_table()
        ## Specific result tables
        # Cost tables
        self._production_cost_per_ton_df = self._empty_base_table()
        self._annuity_on_investment_per_ton_df = self._empty_base_table()
        self._opex_in_euro_per_ton_df = self._empty_base_table()
        self._opex_df = self._empty_base_table()
        self._energy_cost_per_ton_df = self._empty_energy_carrier_table()
        self._steam_cost_per_ton_df = self._empty_energy_carrier_table()
        self._feedstock_cost_per_ton_df = self._empty_energy_carrier_table()
        self._energy_and_feedstock_cost_per_ton_df = self._empty_base_table()
        self._energy_emission_cost_per_ton_df = self._empty_energy_carrier_table()
        self._steam_emission_cost_per_ton_df = self._empty_energy_carrier_table()
        self._energy_and_energy_emission_cost_df = self._empty_energy_carrier_table()
        self._steam_and_steam_emission_cost_df = self._empty_energy_carrier_table()
        self._process_emission_cost_per_ton_df = self._empty_base_table()
        self._production_df = self._empty_base_table()

    def _initialize_virtual_cost_tables(self):
        # Variables for analyzing and comparing process calculations
        ## Process-specific variables for analyzing and comparing
        self._columns_for_comparison = ['id_scenario', 'id_region', 'id_product', 'id_process']
        self._virtual_annuity_per_process_df = self._empty_comparison_table()
        self._virtual_opex_per_process_df = self._empty_comparison_table()
        self._virtual_production_cost_per_ton_per_process_df = self._empty_comparison_table()
        self._virtual_process_emission_costs_per_process_df = self._empty_comparison_table()
        self._virtual_energy_emission_costs_per_process_df = self._empty_comparison_table()
        ## Energy carrier specific variables for analyzing and comparing
        self._virtual_energy_emission_costs_per_energy_carrier_df = self._empty_energy_carrier_comparison_table()
        self._virtual_steam_emission_costs_per_energy_carrier_df = self._empty_energy_carrier_comparison_table()
        self._virtual_energy_costs_per_energy_carrier_df = self._empty_energy_carrier_comparison_table()
        self._virtual_steam_costs_per_energy_carrier_df = self._empty_energy_carrier_comparison_table()
        self._virtual_feedstock_costs_per_energy_carrier_df = self._empty_energy_carrier_comparison_table()

    def visit_region(self, region, year):
        logging.debug('visiting region %s in %s', region.id, year)
        self._region = region
        self._scenario = region.scenario

    def visit_site(self, site, year):
        logging.debug('visiting site %s in %s', site.id, year)
        self._id_site = site.id

    def visit_production_unit(self, production_unit, year):
        logging.debug('visiting production unit %s in %s', production_unit.id, year)
        self._id_production_unit = production_unit.id
        self._production_in_tons = production_unit.production_in_tons

        self._year_of_last_reinvestment = production_unit.previous_year_of_last_reinvestment
        self._previous_process = production_unit.previous_process
        self._new_investment_in_euro = production_unit.new_investment_in_euro(year)

    def visit_product(self, product, year):
        logging.debug('visiting product %s in %s', product.id, year)
        self._id_product = product.id

        self._handle_process_specific_variables(product, year)

        self._handle_energy_carrier_specific_variables(product, year)

    def _handle_process_specific_variables(self, product, year):
        # Process-specific variables for result comparison
        virtual_production_cost_time_series_per_process = product.virtual_production_cost_per_process_for_comparison(
            year
        )
        virtual_process_emission_costs_per_process = product.virtual_process_emission_cost_per_process_for_comparison(
            self._production_in_tons,
            self._region.co2_cost_in_euro_per_ton_c02(year),
        )
        virtual_energy_emission_costs_per_process = product.virtual_energy_emission_cost_per_process_for_comparison(
            year,
            self._region.co2_cost_in_euro_per_ton_c02(year),
        )
        virtual_annuity_per_process = product.virtual_annuity_per_process(year)
        virtual_opex_per_process = product.virtual_opex_per_process(year)
        for id_process, value in virtual_production_cost_time_series_per_process.items():
            self._add_entry_for_process(self._virtual_production_cost_per_ton_per_process_df, id_process, year, value)
        for id_process, value in virtual_process_emission_costs_per_process.items():
            self._add_entry_for_process(self._virtual_process_emission_costs_per_process_df, id_process, year, value)
        for id_process, value in virtual_energy_emission_costs_per_process.items():
            self._add_entry_for_process(self._virtual_energy_emission_costs_per_process_df, id_process, year, value)
        for id_process, value in virtual_annuity_per_process.items():
            self._add_entry_for_process(self._virtual_annuity_per_process_df, id_process, year, value)
        for id_process, value in virtual_opex_per_process.items():
            self._add_entry_for_process(self._virtual_opex_per_process_df, id_process, year, value)

    def _handle_energy_carrier_specific_variables(self, product, year):
        # Energy carrier specific variables for result comparison
        for process in product.available_processes:
            self._handle_energy_demand(process, year)

            self._handle_steam_demand(process, year)

            self._handle_feedstock_demand(process, year)

    def _handle_energy_demand(self, process, year):
        for demand in process.energy_demands:
            energy_carrier = demand.energy_carrier
            id_energy_carrier = energy_carrier.id

            energy_carrier_cost_per_ton = demand.energy_carrier_cost_in_euro_per_ton(year)
            self._add_entry_for_process_and_energy_carrier(
                self._virtual_energy_costs_per_energy_carrier_df,
                process.id,
                id_energy_carrier,
                year,
                energy_carrier_cost_per_ton,
            )

            energy_emission_cost_per_ton_per_carrier = demand.energy_carrier_emission_in_ton_co2_per_ton(
                year,
            ) * self._region.co2_cost_in_euro_per_ton_c02(year)
            self._add_entry_for_process_and_energy_carrier(
                self._virtual_energy_emission_costs_per_energy_carrier_df,
                process.id,
                id_energy_carrier,
                year,
                energy_emission_cost_per_ton_per_carrier,
            )

    def _handle_steam_demand(self, process, year):
        for demand in process.steam_demands:
            energy_carrier = demand.energy_carrier
            id_energy_carrier = energy_carrier.id
            steam_cost_per_ton_per_carrier = demand.steam_cost_in_euro_per_ton(year)
            self._add_entry_for_process_and_energy_carrier(
                self._virtual_steam_costs_per_energy_carrier_df,
                process.id,
                id_energy_carrier,
                year,
                steam_cost_per_ton_per_carrier,
            )

            steam_emission_cost_per_ton_per_carrier = demand.steam_emission_in_ton_co2_per_ton(
                year,
            ) * self._region.co2_cost_in_euro_per_ton_c02(year)
            self._add_entry_for_process_and_energy_carrier(
                self._virtual_steam_emission_costs_per_energy_carrier_df,
                process.id,
                id_energy_carrier,
                year,
                steam_emission_cost_per_ton_per_carrier,
            )

    def _handle_feedstock_demand(self, process, year):
        for demand in process.feedstock_demands:
            energy_carrier = demand.energy_carrier
            id_energy_carrier = energy_carrier.id
            feedstock_cost_per_ton_per_carrier = demand.feedstock_cost_in_euro_per_ton(year)
            self._add_entry_for_process_and_energy_carrier(
                self._virtual_feedstock_costs_per_energy_carrier_df,
                process.id,
                id_energy_carrier,
                year,
                feedstock_cost_per_ton_per_carrier,
            )

    def visit_process(self, process, year):
        logging.debug('visiting process %s in %s', process.id, year)
        self._id_process = process.id

        production_in_tons = self._production_in_tons
        self._add_entry(self._production_df, year, production_in_tons)
        logging.debug('Production %s in %s', production_in_tons, year)

        pipeline_cost_scaling = 1

        process_emission = process.process_emission_in_tons(production_in_tons)
        self._add_entry(self._process_emission_df, year, process_emission)
        logging.debug('Emissions %s in %s', process_emission, year)

        new_investment_in_euro = self._new_investment_in_euro
        self._add_entry(self._investment_df, year, new_investment_in_euro)
        logging.debug('Investment %s in %s', new_investment_in_euro, year)

        annuity_per_ton = process.annuity_on_investment_per_ton(year)
        self._add_entry(self._annuity_on_investment_per_ton_df, year, annuity_per_ton)

        annuity = process.annuity_on_investment_per_ton(year) * production_in_tons
        self._add_entry(self._annuity_on_investment_df, year, annuity)

        opex_per_ton = process.opex_in_euro_per_ton(year)
        self._add_entry(self._opex_in_euro_per_ton_df, year, opex_per_ton)

        opex = process.opex_in_euro_per_ton(year) * production_in_tons
        self._add_entry(self._opex_df, year, opex)

        co2_cost_in_euro_per_ton_c02 = self._region.co2_cost_in_euro_per_ton_c02(year)
        production_cost = process.production_cost_in_euro(
            year,
            production_in_tons,
            co2_cost_in_euro_per_ton_c02,
            pipeline_cost_scaling,
        )
        self._add_entry(self._production_cost_df, year, production_cost)

        process_emission_cost = process_emission * co2_cost_in_euro_per_ton_c02
        self._add_entry(self._process_emission_cost_df, year, process_emission_cost)
        logging.debug('Emissions %s in %s', process_emission, year)

        process_emission_cost_per_ton = (process_emission / production_in_tons) * co2_cost_in_euro_per_ton_c02
        self._add_entry(self._process_emission_cost_per_ton_df, year, process_emission_cost_per_ton)
        logging.debug('Emissions %s in %s', process_emission, year)

        production_cost_in_euro_per_ton = process.production_cost_in_euro_per_ton(year)
        self._add_entry(self._production_cost_per_ton_df, year, production_cost_in_euro_per_ton)

        energy_and_feedstock_cost_per_ton = process.energy_carrier_cost_in_euro_per_ton(year)
        self._add_entry(self._energy_and_feedstock_cost_per_ton_df, year, energy_and_feedstock_cost_per_ton)

        self._handle_energy_demand_for_process(
            co2_cost_in_euro_per_ton_c02,
            process,
            production_in_tons,
            year,
        )

        self._handle_steam_demand_for_process(
            co2_cost_in_euro_per_ton_c02,
            process,
            production_in_tons,
            year,
        )

        self._handle_feedstock_demand_for_process(
            process,
            production_in_tons,
            year,
        )

    def _handle_energy_demand_for_process(self, co2_cost_in_euro_per_ton_c02, process, production_in_tons, year):
        for demand in process.energy_demands:
            energy_carrier = demand.energy_carrier
            id_energy_carrier = energy_carrier.id

            final_energy_demand = production_in_tons * demand.demand_in_gj_per_ton
            self._add_energy_carrier_entry(
                self._final_energy_demand_df,
                id_energy_carrier,
                year,
                final_energy_demand / 3600000,
            )

            energy_cost = demand.energy_carrier_cost_in_euro_per_ton(year) * production_in_tons
            self._add_energy_carrier_entry(self._energy_cost_df, id_energy_carrier, year, energy_cost)

            energy_cost_per_ton = demand.energy_carrier_cost_in_euro_per_ton(year)
            self._add_energy_carrier_entry(self._energy_cost_per_ton_df, id_energy_carrier, year, energy_cost_per_ton)

            energy_emission = demand.energy_carrier_emission_in_ton_co2_per_ton(year) * production_in_tons
            self._add_energy_carrier_entry(self._energy_emission_df, id_energy_carrier, year, energy_emission)

            energy_emission_cost = energy_emission * co2_cost_in_euro_per_ton_c02
            self._add_energy_carrier_entry(self._energy_emission_cost_df, id_energy_carrier, year, energy_emission_cost)

            energy_emission_cost_per_ton = (
                demand.energy_carrier_emission_in_ton_co2_per_ton(year) * co2_cost_in_euro_per_ton_c02
            )
            self._add_energy_carrier_entry(
                self._energy_emission_cost_per_ton_df,
                id_energy_carrier,
                year,
                energy_emission_cost_per_ton,
            )

            energy_and_emission_cost = energy_cost + energy_emission_cost
            self._add_energy_carrier_entry(
                self._energy_and_energy_emission_cost_df,
                id_energy_carrier,
                year,
                energy_and_emission_cost,
            )

    def _handle_steam_demand_for_process(self, co2_cost_in_euro_per_ton_c02, process, production_in_tons, year):
        for demand in process.steam_demands:
            energy_carrier = demand.energy_carrier
            id_energy_carrier = energy_carrier.id

            final_steam_demand = production_in_tons * demand.steam_demand_in_gj_per_ton
            self._add_energy_carrier_entry(
                self._final_steam_demand_df,
                id_energy_carrier,
                year,
                final_steam_demand / 3600000,
            )

            steam_cost = demand.steam_cost_in_euro_per_ton(year) * production_in_tons
            self._add_energy_carrier_entry(self._steam_cost_df, id_energy_carrier, year, steam_cost)

            steam_cost_per_ton = demand.steam_cost_in_euro_per_ton(year)
            self._add_energy_carrier_entry(self._steam_cost_per_ton_df, id_energy_carrier, year, steam_cost_per_ton)

            steam_emission = demand.steam_emission_in_ton_co2_per_ton(year) * production_in_tons
            self._add_energy_carrier_entry(self._steam_emission_df, id_energy_carrier, year, steam_emission)

            steam_emission_cost = steam_emission * co2_cost_in_euro_per_ton_c02
            self._add_energy_carrier_entry(self._steam_emission_cost_df, id_energy_carrier, year, steam_emission_cost)

            steam_emission_cost_per_ton = demand.steam_emission_in_ton_co2_per_ton(year) * co2_cost_in_euro_per_ton_c02
            self._add_energy_carrier_entry(
                self._steam_emission_cost_per_ton_df,
                id_energy_carrier,
                year,
                steam_emission_cost_per_ton,
            )

            steam_and_steam_emission_cost = steam_cost + steam_emission_cost
            self._add_energy_carrier_entry(
                self._steam_and_steam_emission_cost_df,
                id_energy_carrier,
                year,
                steam_and_steam_emission_cost,
            )

    def _handle_feedstock_demand_for_process(self, process, production_in_tons, year):
        for demand in process.feedstock_demands:
            energy_carrier = demand.energy_carrier
            id_energy_carrier = energy_carrier.id

            final_feedstock_demand = production_in_tons * demand.feedstock_demand_in_gj_per_ton
            self._add_energy_carrier_entry(
                self._final_feedstock_demand_df,
                id_energy_carrier,
                year,
                final_feedstock_demand / 3600000,
            )

            feedstock_cost = demand.feedstock_cost_in_euro_per_ton(year) * production_in_tons
            self._add_energy_carrier_entry(self._feedstock_cost_df, id_energy_carrier, year, feedstock_cost)

            feedstock_cost_per_ton = demand.feedstock_cost_in_euro_per_ton(year)
            self._add_energy_carrier_entry(
                self._feedstock_cost_per_ton_df,
                id_energy_carrier,
                year,
                feedstock_cost_per_ton,
            )

    def finalize(self):
        logging.info('finalize')
        output_folder = './output'  # assumes that 'src' is the working directory
        file_utils.create_folder_if_not_exists(output_folder)

        # Unspecific results for individual site and production unit
        ## Energy demands
        self._save(self._final_energy_demand_df, 'final_energy_demand', output_folder)
        self._save(self._final_steam_demand_df, 'final_steam_demand', output_folder)
        self._save(self._final_feedstock_demand_df, 'final_feedstock_demand', output_folder)
        ## Energy costs
        self._save(self._energy_cost_df, 'energy_cost', output_folder)
        self._save(self._steam_cost_df, 'steam_cost', output_folder)
        self._save(self._feedstock_cost_df, 'feedstock_cost', output_folder)
        ## Energy and emission costs
        self._save(self._energy_and_energy_emission_cost_df, 'energy_and_energy_emission_cost', output_folder)
        self._save(self._steam_and_steam_emission_cost_df, 'steam_and_steam_emission_cost', output_folder)
        ## Emission costs
        self._save(self._energy_emission_cost_df, 'energy_emission_cost', output_folder)
        self._save(self._steam_emission_cost_df, 'steam_emission_cost', output_folder)
        self._save(self._process_emission_cost_df, 'process_emission_cost', output_folder)
        ## Emission results
        self._save(self._energy_emission_df, 'energy_emission', output_folder)
        self._save(self._steam_emission_df, 'steam_emission', output_folder)
        self._save(self._process_emission_df, 'process_emission', output_folder)
        ## Total investments
        self._save(self._annuity_on_investment_df, 'annuity', output_folder)
        self._save(self._investment_df, 'investment', output_folder)
        ## Production development
        self._save(self._production_df, 'production', output_folder)
        ## Total production costs
        self._save(self._opex_df, 'opex', output_folder)
        self._save(self._production_cost_df, 'production_cost', output_folder)

        # Specific results per ton of product for individual site and production unit
        ## Production cost components per ton
        self._save(self._annuity_on_investment_per_ton_df, 'annuity_per_ton', output_folder)
        self._save(self._opex_in_euro_per_ton_df, 'opex_per_ton', output_folder)
        self._save(self._process_emission_cost_per_ton_df, 'process_emission_cost_per_ton', output_folder)
        self._save(self._energy_emission_cost_per_ton_df, 'energy_emission_cost_per_ton', output_folder)
        self._save(self._steam_emission_cost_per_ton_df, 'steam_emission_cost_per_ton', output_folder)

        self._save(self._production_cost_per_ton_df, 'production_cost_per_ton', output_folder)
        self._save(self._energy_cost_per_ton_df, 'energy_cost_per_ton', output_folder)
        self._save(self._steam_cost_per_ton_df, 'steam_cost_per_ton', output_folder)
        self._save(self._feedstock_cost_per_ton_df, 'feedstock_cost_per_ton', output_folder)

        # Specific results per ton of product for analysis and comparison
        ## Cost components aggregated
        self._save(
            self._virtual_production_cost_per_ton_per_process_df,
            '_comparison_production_cost_per_ton_per_process_df',
            output_folder,
        )
        self._save(
            self._virtual_process_emission_costs_per_process_df,
            '_comparison_process_emission_costs_per_process_df',
            output_folder,
        )
        self._save(
            self._virtual_energy_emission_costs_per_process_df,
            '_comparison_energy_emission_costs_per_process_df',
            output_folder,
        )
        ## Cost components detailed
        self._save(
            self._virtual_energy_emission_costs_per_energy_carrier_df,
            '_comparison_energy_emission_costs_per_energy_carrier_df',
            output_folder,
        )
        self._save(
            self._virtual_energy_costs_per_energy_carrier_df,
            '_comparison_energy_costs_per_energy_carrier_df',
            output_folder,
        )
        self._save(
            self._virtual_steam_costs_per_energy_carrier_df,
            '_comparison_steam_costs_per_energy_carrier_df',
            output_folder,
        )
        self._save(
            self._virtual_feedstock_costs_per_energy_carrier_df,
            '_comparison_feedstock_costs_per_energy_carrier_df',
            output_folder,
        )
        self._save(self._virtual_annuity_per_process_df, '_comparison_annuity_per_process_df', output_folder)
        self._save(self._virtual_opex_per_process_df, '_comparison_opex_per_process_df', output_folder)

    @staticmethod
    def _save(df, name, output_folder):
        sqlite_path = output_folder + '/output.sqlite'
        connection = sqlite3.connect(sqlite_path)

        excel_path = output_folder + '/' + name + '.xlsx'

        query = 'DROP TABLE IF EXISTS ' + name
        connection.execute(query)
        file_utils.delete_file_if_exists(excel_path)

        if not df.empty:
            TabularResultVisitor._create_empty_table_for_df(df, name, connection)
            df.to_sql(name, connection, index_label=df.index.names, if_exists='append')
            df.to_excel(excel_path, index_label=df.index.names, merge_cells=False)

    @staticmethod
    def _create_empty_table_for_df(df, name, connection):
        query = 'CREATE TABLE ' + name + ' ('
        for column_name in df.index.names:
            query += column_name + ' integer NOT NULL, '

        for column_name in df.columns:
            query += column_name + ' real, '

        query += 'PRIMARY KEY (' + ', '.join(df.index.names) + ')'

        query += ')'

        connection.execute(query)

    def _add_entry(self, df, year, value):
        index_keys = tuple(self._base_row())
        self._add_entry_at(df, index_keys, year, value)

    def _add_entry_for_process(self, df, id_process, year, value):
        index_keys = tuple(self._base_row_for_comparison(id_process))
        self._add_entry_at(df, index_keys, year, value)

    def _add_entry_for_process_and_energy_carrier(self, df, id_process, id_energy_carrier, year, value):
        index_keys = (*self._base_row_for_comparison(id_process), id_energy_carrier)
        self._add_entry_at(df, index_keys, year, value)

    def _add_energy_carrier_entry(self, df, id_energy_carrier, year, value):
        index_keys = (*self._base_row(), id_energy_carrier)
        self._add_entry_at(df, index_keys, year, value)

    @staticmethod
    def _add_entry_at(df, keys, year, value):
        year_column_name = 'Y' + str(year)
        if year_column_name not in df.columns:
            default_values = [None] * len(df)
            df[year_column_name] = default_values

        if keys not in df.index:
            df.loc[keys, year_column_name] = None

        df.loc[keys, year_column_name] = value

    def _empty_base_table(self):
        column_names = self._base_column_names
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_energy_carrier_table(self):
        column_names = [*self._base_column_names, 'id_energy_carrier']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_comparison_table(self):
        column_names = self._columns_for_comparison
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_energy_carrier_comparison_table(self):
        column_names = [*self._columns_for_comparison, 'id_energy_carrier']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _base_row(self):
        return [
            self._scenario,
            self._region.id,
            self._id_site,
            self._id_production_unit,
            self._id_product,
            self._id_process,
        ]

    def _base_row_for_comparison(self, id_process):
        return [
            self._scenario,
            self._region.id,
            self._id_product,
            id_process,
        ]
