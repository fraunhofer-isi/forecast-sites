# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from pandas import DataFrame
from test_utils.isi_mock import Mock, patch

from product.product import Product
from product.product_factory import ProductFactory


@pytest.fixture
def sut():
    mocked_data_interface = Mock()
    return ProductFactory(
        mocked_data_interface,
    )


@patch(ProductFactory._product, 'mocked_by_product')
def test_create_map(sut):
    sut._product_data = DataFrame([{'id': 1, 'name': 'mocked_name'}])
    result = sut.create_map()
    assert result[1] == 'mocked_by_product'


def test_by_product(sut):
    result = sut._product(1, 'mocked_name')
    assert isinstance(result, Product)
