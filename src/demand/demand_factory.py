# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class DemandFactory:
    def __init__(
        self,
        demand_data,
        carriers,
        efficiency_improvement_interpolation_data,
        simulation_options,
    ):
        self._demand_data = demand_data
        self._carriers = carriers
        self._efficiency_improvement_interpolation_data = efficiency_improvement_interpolation_data
        self._simulation_options = simulation_options

    def create(self, id_process):
        demand_entries = self._demand_entries_for_process(id_process)

        demands = []
        for _, row in demand_entries.iterrows():
            demand = self._demand(row)
            demands.append(demand)

        return demands

    def _demand(self, row):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def _demand_entries_for_process(self, id_process):
        try:
            query = 'id_process==' + str(id_process)
            demand_entries = self._demand_data.query(query)
        except KeyError as error:
            message = f'No entries for id_process {id_process}'
            raise KeyError(message) from error

        demand_entries = demand_entries.reset_index()
        del demand_entries['id_process']
        id_column_name = demand_entries.columns[0]
        demand_entries = demand_entries.set_index(id_column_name)
        return demand_entries
