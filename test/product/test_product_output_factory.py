# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from pandas import Series
from test_utils.isi_mock import Mock

from product.product_output import ProductOutput
from product.product_output_factory import ProductOutputFactory

product = Mock()


@pytest.fixture
def sut():
    process_product_demand = Mock()
    products = {1: product}
    return ProductOutputFactory(process_product_demand, products)


def test_output(sut):
    row = Series({'output_in_t_per_process_count': 33}, name=1)
    result = sut._output(row)

    assert isinstance(result, ProductOutput)
    assert result.product == product
    assert result.output_in_t_per_process_count == 33
