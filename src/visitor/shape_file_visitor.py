# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later
import logging

from utils import collection_utils, file_utils
from visitor.visitor import Visitor


class ShapeFileVisitor(Visitor):

    def __init__(self):
        self._output_path = '../output'
        file_utils.create_folder_if_not_exists(self._output_path)

    def visit_region(self, region, year):
        self._export_sites_to_shape_file(region, year)

    def visit_site(self, site, year):
        pass

    def visit_production_unit(self, production_unit, year):
        pass

    def visit_product(self, product, year):
        pass

    def visit_process(self, process, year):
        pass

    def finalize(self):
        pass

    def _export_sites_to_shape_file(self, region, year):
        site_df = region.site_df()
        site_df['year'] = site_df.apply(lambda _site_row: year, axis=1)
        process_ids = site_df.apply(lambda site_row: region.get_process_ids_for_site(site_row.name), axis=1)
        process_ids_string = collection_utils.join_with_comma(process_ids)
        site_df['proc_ids'] = process_ids_string

        self._check_export_column_names(site_df)
        shape_file_path = self._prepare_shape_file_path(year)
        if site_df.empty:
            file_utils.delete_file_if_exists(shape_file_path)
        else:
            site_df.to_file(shape_file_path, driver='ESRI Shapefile')

    def _prepare_shape_file_path(self, year):
        shape_folder_name = 'shape_file_' + str(year)
        shape_folder_path = self._output_path + '/' + shape_folder_name
        file_utils.create_folder_if_not_exists(shape_folder_path)

        return shape_folder_path + '/technology_diffusion.shp'

    @staticmethod
    def _check_export_column_names(data_frame):
        # Length of column names for esri shape files must be <= 10
        # Also see https://support.esri.com/en/technical-article/000022868
        max_number_of_columns = 10
        for column_name in data_frame.columns:
            if len(column_name) > max_number_of_columns:
                message = 'Warning: Length of column name > 10: "' + column_name + '" => Will be shortened for export.'
                logging.warning(message)
