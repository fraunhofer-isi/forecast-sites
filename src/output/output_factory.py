# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class OutputFactory:
    def __init__(self, output_data, carriers):
        self._output_data = output_data
        self._carriers = carriers

    def create(self, id_process):
        output_entries = self._output_entries_for_process(id_process)

        outputs = []
        for _, row in output_entries.iterrows():
            output = self._output(row)
            outputs.append(output)

        return outputs

    def _output(self, row):
        message = 'Needs to be implemented by inheriting classes'
        raise NotImplementedError(message)

    def _output_entries_for_process(self, id_process):
        try:
            query = 'id_process==' + str(id_process)
            output_entries = self._output_data.query(query)
        except KeyError as error:
            message = 'No entries id_product ' + str(id_process)
            raise KeyError(message) from error

        output_entries = output_entries.reset_index()
        del output_entries['id_process']
        id_column_name = output_entries.columns[0]
        output_entries = output_entries.set_index(id_column_name)
        return output_entries
