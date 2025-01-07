# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import MagicMock, patch

from production_unit.production_unit import ProductionUnit
from production_unit.production_unit_factory import ProductionUnitFactory


@pytest.fixture
def sut():
    data_interface = MagicMock()

    production_unit_df = pd.DataFrame(
        {
            'id': [1],
            'id_site': [10],
            'id_product': [10],
            'id_process': [100],
            'production_in_tons': [1000],
            'year_of_last_reinvestment': [2020],
        }
    )
    data_interface.production_unit_mapping = {10: production_unit_df}

    energy_carriers = {1: 'dummy_electricity_energy_carrier', 100: 'dummy_energy_carrier'}
    return ProductionUnitFactory(data_interface, energy_carriers)


def production_unit_init_mock(
    self, id_production_unit, product, process, production_in_tons, year_of_last_reinvestment
):
    self.id = id_production_unit


def test_create_production_units(sut):
    sut._create_production_unit = MagicMock(return_value='dummy_production_unit')

    id_site = 10
    result = sut.create_production_units(id_site)

    assert len(result) == 1
    assert result[0] == 'dummy_production_unit'


@patch.object(ProductionUnit, '__init__', production_unit_init_mock)
def test_create_production_unit(sut):
    sut._product_factory.create_product = MagicMock()
    sut._process_factory.create_process = MagicMock()
    row = {'id': 1, 'id_product': 10, 'id_process': 100, 'production_in_tons': 1000, 'year_of_last_reinvestment': 2020}

    result = sut._create_production_unit(row)
    assert result is not None
