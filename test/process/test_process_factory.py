# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import MagicMock, patch

from process.process import Process
from process.process_factory import ProcessFactory


@pytest.fixture
def sut():
    data_interface = MagicMock()

    process_mapping = pd.DataFrame(
        {
            'id_product': [1],
            'id_process': [10],
            'capex_2015_in_euro_per_ton': 2015,
            'capex_2050_in_euro_per_ton': 2050,
            'opex_2015_in_euro_per_ton': 2015,
            'opex_2050_in_euro_per_ton': 2050,
            'lifetime_in_years': 10,
            'interest_rate': 1,
            'depreciation_period': 1,
            'process_emission_in_ton_co2_per_ton': 1000,
            'efficiency_improvement_2015': 1,
            'efficiency_improvement_2050': 1,
            'investment_funding_2015': 0,
            'investment_funding_2050': 0,
            'investment_flexibility_2015': 0,
            'investment_flexibility_2050': 0,
            'electricity_demand_in_gj_per_ton': 2000,
            'fuel_demand_in_gj_per_ton': 3000,
        },
    )
    process_mapping = process_mapping.set_index(['id_product', 'id_process'])

    data_interface.product_process_mapping = process_mapping

    energy_carrier = MagicMock()

    process_factory = ProcessFactory(data_interface, energy_carrier)
    return process_factory


def process_init_mock(
    self,
    id_process,
    _capex_2015_in_euro_per_ton,
    _capex_2050_in_euro_per_ton,
    _opex_2015_in_euro_per_ton,
    _opex_2050_in_euro_per_ton,
    _lifetime_in_years,
    _interest_rate,
    _depreciation_period,
    _emission_factor_in_ton_co2_per_ton,
    _efficiency_improvement_2015,
    _efficiency_improvement_2050,
    _investment_funding_2015,
    _investment_funding_2050,
    _investment_flexibility_2015,
    _investment_flexibility_2050,
    _energy_demands,
):
    self.id = id_process


def test_create_processes(sut):
    sut.create_process = MagicMock(return_value='mocked_process')
    process_ids = [39, 12, 39, 32]
    id_product = 2
    processes = sut.create_processes(id_product, process_ids)
    for process in processes:
        assert process == 'mocked_process'


@patch.object(Process, '__init__', process_init_mock)
def test_create_process(sut):
    id_product = 1
    id_process = 10
    process = sut.create_process(id_product, id_process)
    assert process.id == 10
