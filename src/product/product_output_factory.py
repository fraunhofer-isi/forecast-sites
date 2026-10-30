# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from output.output_factory import OutputFactory
from product.product_output import ProductOutput


class ProductOutputFactory(OutputFactory):
    def __init__(self, process_product_output, products):
        super().__init__(process_product_output, products)

    def _output(self, row):
        id_product = row.name
        product = self._carriers[id_product]

        output_in_t_per_process_count = row['output_in_t_per_process_count']

        output = ProductOutput(product, output_in_t_per_process_count)
        return output
