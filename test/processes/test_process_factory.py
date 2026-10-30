# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from mock import patch as original_patch
from pandas import DataFrame
from test_utils.isi_mock import Mock, patch

from by_product.by_product_feedstock_demand_factory import (
    ByProductFeedstockDemandFactory,
)
from by_product.by_product_output_factory import ByProductOutputFactory
from energy_carrier.energy_carrier_energy_demand_factory import (
    EnergyCarrierEnergyDemandFactory,
)
from energy_carrier.energy_carrier_feedstock_demand_factory import (
    EnergyCarrierFeedstockDemandFactory,
)
from interpolation.interpolation_data import InterpolationData
from processes.process import Process
from processes.process_factory import ProcessFactory
from product.product_feedstock_demand_factory import ProductFeedstockDemandFactory
from product.product_output_factory import ProductOutputFactory


@pytest.fixture
@patch(EnergyCarrierEnergyDemandFactory.__init__, None)
@patch(EnergyCarrierFeedstockDemandFactory.__init__, None)
@patch(ProductFeedstockDemandFactory.__init__, None)
@patch(ProductOutputFactory.__init__, None)
@patch(ByProductFeedstockDemandFactory.__init__, None)
@patch(ByProductOutputFactory.__init__, None)
def sut():
    data_interface = Mock()

    process_factory = ProcessFactory(
        data_interface,
        'mocked_energy_carriers',
        'mocked_products',
        'mocked_by_products',
        'mocked_simulation_options',
    )
    return process_factory


def test_construction(sut):
    assert sut is not None


def test_efficiency_improvement_interpolation_data(sut):
    id_process = 1
    sut._process_data = DataFrame(
        [
            {
                'id_process': id_process,
                'efficiency_improvement_start_year': 0.1,
                'efficiency_improvement_end_year': 0.5,
            }
        ]
    ).set_index('id_process')

    result = sut._efficiency_improvement_interpolation_data(id_process)

    assert isinstance(result, InterpolationData)
    assert result.value_for_start_year == 0.1
    assert result.value_for_end_year == 0.5


@patch(ProcessFactory._create, 'mocked_process')
def test_create_map(sut):
    sut._process_data = DataFrame([{'id_process': 1}]).set_index('id_process')
    result = sut.create_map()
    assert result[1] == 'mocked_process'


@patch(Process.__init__, None)
@patch(ProcessFactory._create_outputs, 'mocked_outputs')
@patch(ProcessFactory._create_demands, 'mocked_demands')
def test_create(sut):
    id_process = 10
    result = sut._create(id_process)
    assert isinstance(result, Process)


def test_create_demands(sut):
    # Patch factory create methods to return mocked lists
    with (
        original_patch(
            'energy_carrier.energy_carrier_energy_demand_factory.EnergyCarrierEnergyDemandFactory.create',
            Mock(['mocked_energy_carrier_energy_demand']),
        ),
        original_patch(
            'energy_carrier.energy_carrier_feedstock_demand_factory.EnergyCarrierFeedstockDemandFactory.create',
            Mock(['mocked_energy_carrier_feedstock_demand']),
        ),
        original_patch(
            'by_product.by_product_feedstock_demand_factory.ByProductFeedstockDemandFactory.create',
            Mock(['mocked_by_product_feedstock_demand']),
        ),
        original_patch(
            'product.product_feedstock_demand_factory.ProductFeedstockDemandFactory.create',
            Mock(['mocked_product_feedstock_demand']),
        ),
        patch(ProcessFactory._efficiency_improvement_interpolation_data, lambda _self, _id: InterpolationData(0, 0)),
    ):
        result = sut._create_demands(1)

    assert result == [
        'mocked_energy_carrier_energy_demand',
        'mocked_energy_carrier_feedstock_demand',
        'mocked_by_product_feedstock_demand',
        'mocked_product_feedstock_demand',
    ]


def test_create_outputs(sut):
    sut._product_output_factory.create = Mock(['mocked_product_output'])
    sut._by_product_output_factory.create = Mock(['mocked_by_product_output'])

    result = sut._create_outputs(1)

    assert result == [
        'mocked_product_output',
        'mocked_by_product_output',
    ]


def test_sector_ids(sut):
    id_process = 1
    sut._process_sector_mapping = DataFrame(
        [
            {'id_process': id_process, 'id_sector': 1},
            {'id_process': id_process, 'id_sector': 2},
        ]
    )

    result = sut._sector_ids(id_process)

    assert result == (1, 2)
