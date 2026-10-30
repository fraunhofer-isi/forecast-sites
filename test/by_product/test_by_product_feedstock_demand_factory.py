# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from pandas import Series
from test_utils.isi_mock import Mock

from by_product.by_product_feedstock_demand import ByProductFeedstockDemand
from by_product.by_product_feedstock_demand_factory import (
    ByProductFeedstockDemandFactory,
)
from interpolation.interpolation_data import InterpolationData

by_product = Mock()

efficiency_improvement_interpolation_data = InterpolationData(0, 0)
simulation_options = {
    'start_year': 2000,
    'interim_year': 2025,
    'end_year': 2050,
}


@pytest.fixture
def sut():
    process_by_product_demand = Mock()
    by_products = {1: by_product}
    return ByProductFeedstockDemandFactory(
        process_by_product_demand,
        by_products,
        efficiency_improvement_interpolation_data,
        simulation_options,
    )


def test_demand(sut):
    row = Series({'demand_in_t_per_process_count': 33}, name=1)
    result = sut._demand(row)

    assert isinstance(result, ByProductFeedstockDemand)
    assert result.by_product == by_product
    year = 2000
    assert result.demand_in_t_per_process_count(year) == 33
