# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging
import sqlite3

import pandas as pd

from result.result_table_writer import ResultTableWriter
from result.visitor.indexing_visitor import IndexingVisitor
from result.visitor.result_table_kind import ResultTableKind
from utils import data_frame_utils, file_utils, time_utils


class TabularVisitor(IndexingVisitor):
    # Serves as a base class for visitors that store
    # results in tabular form.

    def __init__(self, simulation_options):
        super().__init__(simulation_options)
        self._writer = ResultTableWriter()

        self._initialize()

    def _initialize(self):
        # Should be overridden by inheriting classes to initialize
        # absolute and specific result tables.
        pass

    @property
    def _absolute_results(self):
        """Provide backward compatibility access to writer's absolute results."""
        return self._writer.absolute_results

    @_absolute_results.setter
    def _absolute_results(self, value):
        """Allow setting absolute results for backward compatibility."""
        self._writer.absolute_results = value

    @property
    def _specific_results(self):
        """Provide backward compatibility access to writer's specific results."""
        return self._writer.specific_results

    @_specific_results.setter
    def _specific_results(self, value):
        """Allow setting specific results for backward compatibility."""
        self._writer.specific_results = value

    def _initialize_tables(self, target_results, table_schema):
        """
        Create one empty table per entry of a declarative table schema.

        Args:
            target_results: Either self._absolute_results or self._specific_results.
            table_schema: Sequence of (table_name, ResultTableKind) pairs.

        """
        create_empty_table_by_kind = self._empty_table_factory_by_kind()
        for table_name, table_kind in table_schema:
            create_empty_table = create_empty_table_by_kind[table_kind]
            target_results[table_name] = create_empty_table()

    def _empty_table_factory_by_kind(self):
        return {
            ResultTableKind.REGION: self._empty_region_table,
            ResultTableKind.REGION_ENERGY_CARRIER: self._empty_region_energy_carrier_table,
            ResultTableKind.SECTOR: self._empty_sector_table,
            ResultTableKind.SECTOR_ENERGY_CARRIER: self._empty_sector_energy_carrier_table,
            ResultTableKind.SITE: self._empty_site_table,
            ResultTableKind.SITE_ENERGY_CARRIER: self._empty_site_energy_carrier_table,
            ResultTableKind.SITE_PRODUCT: self._empty_site_product_table,
            ResultTableKind.SITE_BY_PRODUCT: self._empty_site_by_product_table,
            ResultTableKind.PRODUCTION_UNIT: self._empty_production_unit_table,
            ResultTableKind.PRODUCTION_UNIT_ENERGY_CARRIER: self._empty_production_unit_energy_carrier_table,
            ResultTableKind.PRODUCTION_UNIT_PRODUCT: self._empty_production_unit_product_table,
            ResultTableKind.PRODUCTION_UNIT_BY_PRODUCT: self._empty_production_unit_by_product_table,
            ResultTableKind.BASE: self._empty_base_table,
            ResultTableKind.ENERGY_CARRIER: self._empty_energy_carrier_table,
            ResultTableKind.PRODUCT: self._empty_product_table,
            ResultTableKind.BY_PRODUCT: self._empty_by_product_table,
        }

    def finalize(self):
        logging.info('Finalizing tabular results...')
        output_directory = self._simulation_options['output_directory']
        file_utils.create_folder_if_not_exists(output_directory)

        self._finalize_results(output_directory)

        logging.info('... finished tabular results.')

    @staticmethod
    def _save(df, name, output_folder):
        if df.empty:
            message = f'Table {name} is empty.'
            logging.info(message)

        merged_df = TabularVisitor._merge_with_existing(df, name, output_folder)
        TabularVisitor._save_as_sqlite_table(merged_df, name, output_folder)
        TabularVisitor._save_as_excel_file(merged_df, name, output_folder)

    @staticmethod
    def _merge_with_existing(df, name, output_folder):
        sqlite_path = output_folder + '/output.sqlite'
        try:
            with sqlite3.connect(sqlite_path) as connection:
                existing_df = TabularVisitor._read_existing_table(connection, name, df)
        except sqlite3.OperationalError:
            return df
        return TabularVisitor._merge_results(existing_df, df)

    @staticmethod
    def _read_existing_table(connection, name, reference_df):
        try:
            existing_df = pd.read_sql_query(f'SELECT * FROM `{name}`', connection)
        except (sqlite3.OperationalError, pd.errors.DatabaseError):
            return reference_df.iloc[0:0].copy()

        if existing_df.empty:
            return reference_df.iloc[0:0].copy()

        index_names = [name for name in reference_df.index.names if name is not None]
        if index_names:
            existing_df = existing_df.set_index(index_names)
        return existing_df

    @staticmethod
    def _merge_results(existing_df, new_df):
        if existing_df.empty:
            return new_df
        if new_df.empty:
            return existing_df

        kept_existing = existing_df.loc[~existing_df.index.isin(new_df.index)]
        all_columns = kept_existing.columns.union(new_df.columns)
        kept_existing = kept_existing.reindex(columns=all_columns)
        new_df = new_df.reindex(columns=all_columns)
        merged_df = pd.concat([kept_existing, new_df])
        return merged_df.sort_index()

    @staticmethod
    def _save_as_sqlite_table(df, name, output_folder):
        sqlite_path = output_folder + '/output.sqlite'
        with sqlite3.connect(sqlite_path) as connection:
            query = 'DROP TABLE IF EXISTS ' + name
            connection.execute(query)
            TabularVisitor._create_empty_table(df, name, connection)
            if not df.empty:
                df.to_sql(name, connection, index_label=df.index.names, if_exists='append')

    @staticmethod
    def _save_as_excel_file(df, name, output_folder):
        excel_path = output_folder + '/' + name + '.xlsx'
        file_utils.delete_file_if_exists(excel_path)
        df.to_excel(excel_path, index_label=df.index.names, merge_cells=False)

    @staticmethod
    def _create_empty_table(df, name, connection):
        query = 'CREATE TABLE ' + name + ' ('
        for column_name in df.index.names:
            query += column_name + ' integer NOT NULL, '

        for column_name in df.columns:
            query += column_name + ' real, '

        query += 'PRIMARY KEY (' + ', '.join(df.index.names) + ')'

        query += ')'

        connection.execute(query)

    @staticmethod
    def _add_entry_at(df, keys, year, value):
        ResultTableWriter.add_entry_at(df, keys, year, value)

    @staticmethod
    def _add_or_accumulate_entry_at(df, keys, year, value):
        ResultTableWriter.add_or_accumulate_entry_at(df, keys, year, value)

    def _site_row(self):
        return [
            self._id_scenario,
            self._region.id,
            self._id_site,
        ]

    def _production_unit_row(self):
        site_row = self._site_row()
        return [
            *site_row,
            self._id_production_unit,
        ]

    def _base_row(self):
        production_unit_row = self._production_unit_row()
        return [
            *production_unit_row,
            self._id_sub_production_unit,
            self._id_process,
        ]

    def _empty_region_energy_carrier_table(self):
        column_names = [*self._region_indices, 'id_energy_carrier']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_region_table(self):
        column_names = self._region_indices
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_sector_energy_carrier_table(self):
        column_names = [*self._region_indices, 'id_sector', 'id_energy_carrier']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_sector_table(self):
        column_names = [*self._region_indices, 'id_sector']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_site_table(self):
        column_names = self._site_indices
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_site_energy_carrier_table(self):
        column_names = [*self._site_indices, 'id_energy_carrier']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_site_product_table(self):
        column_names = [*self._site_indices, 'id_product']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_site_by_product_table(self):
        column_names = [*self._site_indices, 'id_by_product']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_production_unit_table(self):
        column_names = self._production_unit_indices
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_production_unit_energy_carrier_table(self):
        column_names = [*self._production_unit_indices, 'id_energy_carrier']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_production_unit_product_table(self):
        column_names = [*self._production_unit_indices, 'id_product']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_production_unit_by_product_table(self):
        column_names = [*self._production_unit_indices, 'id_by_product']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_base_table(self):
        column_names = self._base_indices
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_energy_carrier_table(self):
        column_names = [*self._base_indices, 'id_energy_carrier']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_product_table(self):
        column_names = [*self._base_indices, 'id_product']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _empty_by_product_table(self):
        column_names = [*self._base_indices, 'id_by_product']
        df = pd.DataFrame(columns=column_names)
        df = df.set_index(column_names)
        return df

    def _add_region_energy_carrier_entry_or_accumulate(self, df, id_energy_carrier, year, value):
        keys = (self._id_scenario, self._id_region, id_energy_carrier)
        self._add_or_accumulate_entry_at(df, keys, year, value)

    def _add_sector_energy_carrier_entry_or_accumulate(self, df, id_energy_carrier, year, value):
        keys = (self._id_scenario, self._id_region, self._id_sector, id_energy_carrier)
        self._add_or_accumulate_entry_at(df, keys, year, value)

    def _add_sector_energy_carrier_entry(self, df, id_sector, id_energy_carrier, year, value):
        keys = (self._id_scenario, self._id_region, id_sector, id_energy_carrier)
        self._add_entry_at(df, keys, year, value)

    def _add_region_entry_or_accumulate(self, df, year, value):
        keys = (self._id_scenario, self._id_region)
        self._add_or_accumulate_entry_at(df, keys, year, value)

    def _add_sector_entry_or_accumulate(self, df, year, value):
        keys = (self._id_scenario, self._id_region, self._id_sector)
        self._add_or_accumulate_entry_at(df, keys, year, value)

    def _add_site_entry(self, df, year, value):
        index_keys = tuple(self._site_row())
        self._add_entry_at(df, index_keys, year, value)

    def _add_site_energy_carrier_entry(self, df, id_energy_carrier, year, value):
        index_keys = (*self._site_row(), id_energy_carrier)
        self._add_entry_at(df, index_keys, year, value)

    def _add_site_product_entry(self, df, id_product, year, value):
        index_keys = (*self._site_row(), id_product)
        self._add_entry_at(df, index_keys, year, value)

    def _add_site_by_product_entry(self, df, id_by_product, year, value):
        index_keys = (*self._site_row(), id_by_product)
        self._add_entry_at(df, index_keys, year, value)

    def _add_production_unit_entry(self, df, year, value):
        index_keys = tuple(self._production_unit_row())
        self._add_entry_at(df, index_keys, year, value)

    def _add_production_unit_energy_carrier_entry(self, df, id_energy_carrier, year, value):
        index_keys = (*self._production_unit_row(), id_energy_carrier)
        self._add_entry_at(df, index_keys, year, value)

    def _add_production_unit_product_entry(self, df, id_product, year, value):
        index_keys = (*self._production_unit_row(), id_product)
        self._add_entry_at(df, index_keys, year, value)

    def _add_production_unit_by_product_entry(self, df, id_by_product, year, value):
        index_keys = (*self._production_unit_row(), id_by_product)
        self._add_entry_at(df, index_keys, year, value)

    def _add_entry(self, df, year, value):
        index_keys = tuple(self._base_row())
        self._add_entry_at(df, index_keys, year, value)

    def _add_energy_carrier_entry(self, df, id_energy_carrier, year, value):
        index_keys = (*self._base_row(), id_energy_carrier)
        self._add_entry_at(df, index_keys, year, value)

    def _add_product_entry(self, df, id_product, year, value):
        index_keys = (*self._base_row(), id_product)
        self._add_entry_at(df, index_keys, year, value)

    def _add_by_product_entry(self, df, id_by_product, year, value):
        index_keys = (*self._base_row(), id_by_product)
        self._add_entry_at(df, index_keys, year, value)

    def _finalize_results(self, output_folder):
        expected_years = time_utils.create_time_span(
            start_year=self._simulation_options['start_year'],
            end_year=self._simulation_options['end_year'],
            year_increment=self._simulation_options['year_increment'],
        )

        for name, df in self._absolute_results.items():
            # some year columns might be missing if no data was recorded for these years
            # we fill those columns with None values to ensure consistent table structure
            consistent_df = data_frame_utils.ensure_year_columns_exist(df, expected_years)

            self._save(consistent_df, name, output_folder)

        for name, df in self._specific_results.items():
            # some year columns might be missing if no data was recorded for these years
            # we fill those columns with None values to ensure consistent table structure
            consistent_df = data_frame_utils.ensure_year_columns_exist(df, expected_years)

            self._save(consistent_df, name, output_folder)
