# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import Mock

import pytest

from product.product import Product


@pytest.fixture
def sut():
    product_id = 39
    process1 = Mock()
    process1.production_cost.return_value = 53.0

    available_processes = [process1]
    for cost in [26.0, 47, 2, 0]:
        process = Mock()
        process.production_cost.return_value = cost
        available_processes.append(process)

    product = Product(product_id, available_processes)
    return product


def test_accept(sut):
    visitor = Mock(return_value=None)
    year = 2015
    sut.accept(visitor, year)
    assert visitor.visit_product.called
