# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from processes.installed_process import InstalledProcess
from sub_production_unit.sub_production_unit import SubProductionUnit


class SubProductionUnitFactory:
    def __init__(
        self,
        data_interface,
        process_map,
    ):
        self._data_interface = data_interface
        self._process_map = process_map
        self._next_ids = {}

    def create_for_start_year(self, id_production_unit):
        sub_production_unit_data = self._sub_production_unit_data(id_production_unit)
        if len(sub_production_unit_data) == 0:
            message = f'No sub production units found for production unit {id_production_unit}.'
            raise ValueError(message)

        used_process_ids = set()

        sub_production_units = []
        for id_sub_production_unit, row in sub_production_unit_data.iterrows():
            id_process = int(row['id_process'])
            year_of_last_reinvestment = row['year_of_last_reinvestment']
            process_execution_count = row['process_execution_count_for_start_year']
            max_process_execution_count = row['max_process_execution_count']

            sub_production_unit = SubProductionUnit(
                id_sub_production_unit,
                id_production_unit,
                process_execution_count,
                max_process_execution_count,
                year_of_last_reinvestment,
            )

            process = self._process_map[id_process]
            used_process_ids.add(id_process)

            installed_process = InstalledProcess(process, sub_production_unit)
            sub_production_unit.installed_process = installed_process

            sub_production_units.append(sub_production_unit)

        return sub_production_units

    def create_sub_production_unit_for_process_option(
        self,
        process_option,
        process_execution_count,
        production_unit,
        year_of_last_reinvestment,
    ):
        process = process_option.process
        if isinstance(process, InstalledProcess):
            message = (
                'InstalledProcess should not occur here because existing sub production units'
                ' should be found and used for those processes!'
            )
            raise KeyError(message)

        id_production_unit = production_unit.id
        id_sub_production_unit = self._unique_id(id_production_unit)

        max_process_execution_count = process_execution_count

        sub_production_unit = SubProductionUnit(
            id_sub_production_unit,
            id_production_unit,
            process_execution_count,
            max_process_execution_count,
            year_of_last_reinvestment,
        )
        sub_production_unit.installed_process = InstalledProcess(process, sub_production_unit)
        return sub_production_unit

    def _unique_id(self, id_production_unit):
        if id_production_unit not in self._next_ids:
            self._next_ids[id_production_unit] = 1000_000 + id_production_unit * 10_000

        next_id = self._next_ids[id_production_unit]
        self._next_ids[id_production_unit] += 1
        return next_id

    def _sub_production_unit_data(self, id_production_unit):
        df = self._data_interface.production_unit_sub_production_unit_mapping[id_production_unit]
        return df
