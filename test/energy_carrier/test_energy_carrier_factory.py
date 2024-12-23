# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import MagicMock, patch

from energy_carrier.energy_carrier import EnergyCarrier
from energy_carrier.energy_carrier_factory import EnergyCarrierFactory


@pytest.fixture
def sut():
    data_interface = MagicMock()
    data_interface.id_scenario = 1
    data_interface.id_region = 10
    data_interface.energy_carrier_data = pd.DataFrame({'id': ['energy_carrier_id'], 'name': ['energy_carrier_name']})

    energy_carrier_mapping = pd.DataFrame(
        {
            'id_scenario': [1],
            'id_region': [10],
            'id_energy_carrier': [100],
            'cost_2015_in_euro_per_gj': 2015,
            'cost_2030_in_euro_per_gj': 2030,
            'cost_2050_in_euro_per_gj': 2050,
            'emission_2015_in_ton_per_gj': 2015,
            'emission_2050_in_ton_per_gj': 2050,
            'availability_2015_in_gj': 2015,
            'availability_2050_in_gj': 2050,
            'subsidies_2015_in_euro_per_gj': 2015,
            'subsidies_2030_in_euro_per_gj': 2030,
            'subsidies_2050_in_euro_per_gj': 2050,
            'taxes_2015_in_euro_per_gj': 2015,
            'taxes_2050_in_euro_per_gj': 2050,
        }
    )
    energy_carrier_mapping.set_index(['id_scenario', 'id_region', 'id_energy_carrier'], inplace=True)
    data_interface.energy_carrier_cost_mapping = energy_carrier_mapping

    energy_carrier_factory = EnergyCarrierFactory(data_interface)
    return energy_carrier_factory


def energy_carrier_init_mock(
    self,
    id_energy_carrier,
    name,
    cost_2015_in_euro_per_gj,
    cost_2030_in_euro_per_gj,
    cost_2050_in_euro_per_gj,
    emission_2015_in_ton_per_gj,
    emission_2050_in_ton_per_gj,
    availability_2015_in_gj,
    availability_2050_in_gj,
    subsidies_2015_in_euro_per_gj,
    subsidies_2030_in_euro_per_gj,
    subsidies_2050_in_euro_per_gj,
    taxes_2015_in_euro_per_gj,
    taxes_2050_in_euro_per_gj,
):
    self.name = name
    self.id_energy_carrier = id_energy_carrier
    self.cost_2015_in_euro_per_gj = cost_2015_in_euro_per_gj
    self.cost_2030_in_euro_per_gj = cost_2030_in_euro_per_gj
    self.cost_2050_in_euro_per_gj = cost_2050_in_euro_per_gj
    self.emission_2015_in_ton_per_gj = emission_2015_in_ton_per_gj
    self.emission_2050_in_ton_per_gj = emission_2050_in_ton_per_gj
    self.availability_2015_in_gj = availability_2015_in_gj
    self.availability_2050_in_gj = availability_2050_in_gj
    self.subsidies_2015_in_euro_per_gj = subsidies_2015_in_euro_per_gj
    self.subsidies_2030_in_euro_per_gj = subsidies_2030_in_euro_per_gj
    self.subsidies_2050_in_euro_per_gj = subsidies_2050_in_euro_per_gj
    self.taxes_2015_in_euro_per_gj = taxes_2015_in_euro_per_gj
    self.taxes_2050_in_euro_per_gj = taxes_2050_in_euro_per_gj


def test_create_energy_carrier_map(sut):
    sut._create_energy_carrier = MagicMock(return_value='dummy_energy_carrier')
    result = sut.create_energy_carrier_map()
    assert isinstance(result, dict)

    energy_carrier = result['energy_carrier_id']
    assert energy_carrier == 'dummy_energy_carrier'


@patch.object(EnergyCarrier, '__init__', energy_carrier_init_mock)
def test_create_energy_carrier(sut):
    id_energy_carrier = 100
    name = 'dummy'
    result = sut._create_energy_carrier(id_energy_carrier, name)
    assert result.name == name
