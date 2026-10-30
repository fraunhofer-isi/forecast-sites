# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from by_product.by_product_output import ByProductOutput
from output.output_factory import OutputFactory


class ByProductOutputFactory(OutputFactory):
    def __init__(self, process_by_product_output, by_products):
        super().__init__(process_by_product_output, by_products)

    def _output(self, row):
        id_by_product = row.name
        by_product = self._carriers[id_by_product]

        output_in_t_per_process_count = row['output_in_t_per_process_count']

        output = ByProductOutput(by_product, output_in_t_per_process_count)
        return output
