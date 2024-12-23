# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import MagicMock

import pytest

from product.product import Product
from product.product_factory import ProductFactory


@pytest.fixture
def sut():
    data_interface = MagicMock()
    process_factory = MagicMock()
    process_factory.__getitem__.return_value = [1, 1]
    product_factory = ProductFactory(data_interface, process_factory)
    return product_factory


def test_create_product(sut):
    product_id = 1
    product = sut.create_product(product_id)
    assert isinstance(product, Product)
