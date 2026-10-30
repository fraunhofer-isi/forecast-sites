# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from energy_carrier.energy_carrier_output import EnergyCarrierOutput
from output.output_factory import OutputFactory


class EnergyCarrierOutputFactory(OutputFactory):
    def __init__(self, process_energy_carrier_output, energy_carriers):
        super().__init__(process_energy_carrier_output, energy_carriers)

    def _output(self, row):
        id_energy_carrier = row.name
        energy_carrier = self._carriers[id_energy_carrier]

        output_in_gj_per_process_count = row['output_in_gj_per_process_count']

        output = EnergyCarrierOutput(energy_carrier, output_in_gj_per_process_count)
        return output
