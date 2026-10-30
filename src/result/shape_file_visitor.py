# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from result.visitor.visitor import Visitor
from utils import collection_utils, file_utils

# ESRI Shapefile format hard-limits string field values to 254 characters.
# See https://support.esri.com/en/technical-article/000022868
ESRI_MAX_FIELD_LENGTH = 254
_ELLIPSIS = ', ..., '


class ShapeFileVisitor(Visitor):
    def __init__(self, simulation_options):
        self._simulation_options = simulation_options
        self._output_directory = simulation_options['output_directory']
        file_utils.create_folder_if_not_exists(self._output_directory)

    def enter_site(self, _site, _year):
        pass

    def enter_production_unit(self, _production_unit, _year):
        pass

    def enter_sub_production_unit(self, _production_unit, _year):
        pass

    @staticmethod
    def _shorten_column_names(site_data):
        site_df = site_data.copy(deep=True)
        # The ESRI Shapefile format restricts column names to a maximum of 10 characters.
        shorter_column_names = {
            'id_company': 'id_comp',
        }
        site_df = site_df.rename(columns=shorter_column_names)
        ShapeFileVisitor._check_length_of_column_names(site_df)
        return site_df

    @staticmethod
    def _check_length_of_column_names(site_df):
        max_column_length = 10
        for column_name in site_df.columns:
            if len(column_name) > max_column_length:
                message = "Length of column name must be <= 10 for esri export: '{column_name}'."
                raise ValueError(message)

    @staticmethod
    def _check_export_column_names(data_frame):
        # Length of column names for esri shape files must be <= 10
        # Also see https://support.esri.com/en/technical-article/000022868
        max_number_of_columns = 10
        for column_name in data_frame.columns:
            if len(column_name) > max_number_of_columns:
                message = 'Warning: Length of column name > 10: "' + column_name + '" => Will be shortened for export.'
                logging.warning(message)

    @staticmethod
    def _check_crs(site_df):
        if not hasattr(site_df, 'crs') or site_df.crs is None:
            message = "CRS is missing in geopandas DataFrame. Use for example site_df.set_crs('EPSG:4326')."
            raise ValueError(message)

    @staticmethod
    def _filter_sites_for_region(site_df, region):
        existing_site_ids = {site.id for site in region.sites}
        site_df = site_df.loc[site_df.index.isin(existing_site_ids)]
        return site_df

    @staticmethod
    def _set_year(site_df, year):
        site_df['year'] = site_df.apply(lambda _site_row: year, axis=1)
        return site_df

    @staticmethod
    def _set_process_ids(site_df, region):
        process_id_strings = site_df.apply(
            lambda site_row: ShapeFileVisitor._process_ids_as_string(region, site_row.name),
            axis=1,
        )

        # length of column name must be <= 10 for esri export
        site_df['proc_ids'] = process_id_strings
        return site_df

    @staticmethod
    def _process_ids_as_string(region, id_site):
        process_ids = region.process_ids_for_site(id_site)
        return ShapeFileVisitor._join_within_limit(process_ids)

    @staticmethod
    def _join_within_limit(ids):
        """Join ids as comma-separated string, staying within ESRI_MAX_FIELD_LENGTH.

        When all ids fit, the result is identical to join_with_comma(ids).
        When they do not all fit, the result is '<first ids>, ..., <last id>'
        so both ends of the list are always visible in the GIS tool.
        """
        if not ids:
            return ''

        full = collection_utils.join_with_comma(ids)
        if len(full) <= ESRI_MAX_FIELD_LENGTH:
            return full

        last = str(ids[-1])
        suffix = _ELLIPSIS + last

        if len(suffix) >= ESRI_MAX_FIELD_LENGTH:
            # Defensive: last id alone fills the field (impossible for integer ids).
            return full[:ESRI_MAX_FIELD_LENGTH - len(', ...')] + ', ...'

        budget = ESRI_MAX_FIELD_LENGTH - len(suffix)
        prefix = ''
        # The loop's normal-exit (iterator exhausted without `break`) is unreachable:
        # if every id in ids[:-1] fit within `budget`, the full join would also fit
        # within ESRI_MAX_FIELD_LENGTH, contradicting the `len(full) <= ...` guard
        # above. The loop therefore always exits via `break`; the exhausted-iterator
        # arc is excluded from branch coverage.
        for id_ in ids[:-1]:  # pragma: no branch
            entry = str(id_)
            candidate = entry if not prefix else prefix + ', ' + entry
            if len(candidate) <= budget:
                prefix = candidate
            else:
                break

        return prefix + suffix

    def enter_region(self, region, year):
        self._export_sites_to_shape_file(region, year)

    def _export_sites_to_shape_file(self, region, year):
        site_df = self._site_data_frame(region, year)
        shape_file_path = self._shape_file_path(region, year)
        if site_df.empty:
            file_utils.delete_file_if_exists(shape_file_path)
        else:
            site_df.to_file(shape_file_path, driver='ESRI Shapefile')

    def _site_data_frame(self, region, year):
        site_data = region.site_data
        site_df = self._shorten_column_names(site_data)
        site_df = self._filter_sites_for_region(site_df, region)
        site_df = self._set_year(site_df, year)
        site_df = self._set_process_ids(site_df, region)

        self._check_export_column_names(site_df)
        self._check_crs(site_df)

        return site_df

    def _shape_file_path(self, region, year):
        shape_folder_name = f'shape_file_{year}_scenario_{region.id_scenario}'
        shape_folder_path = self._output_directory + '/' + shape_folder_name
        file_utils.create_folder_if_not_exists(shape_folder_path)

        return shape_folder_path + '/forecast_sites.shp'

    def finalize(self):
        pass
