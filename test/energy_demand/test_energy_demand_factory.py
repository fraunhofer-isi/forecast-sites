# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pandas as pd
import pytest
from mock import MagicMock, patch

from energy_demand.energy_demand import EnergyDemand
from energy_demand.energy_demand_factory import EnergyDemandFactory


@pytest.fixture
def sut():
    data_interface = MagicMock()
    data_interface.energy_demand_data = pd.DataFrame({'id': ['energy_demand_id'], 'name': ['energy_demand_name']})

    energy_carrier_mapping = pd.DataFrame(
        {
            'id_product': [1],
            'id_process': [10],
            'id_energy_carrier': 100,
            'fuel_share': 0.5,
        },
    )
    energy_carrier_mapping = energy_carrier_mapping.set_index(['id_product', 'id_process', 'id_energy_carrier'])
    data_interface.process_energy_carrier_mapping = energy_carrier_mapping

    energy_carriers = {1: 'dummy_electricity_energy_carrier', 100: 'dummy_energy_carrier'}
    return EnergyDemandFactory(data_interface, energy_carriers)


def energy_demand_init_mock(
    self,
    energy_carrier,
    _demand_in_gj_per_ton,
):
    self.energy_carrier = energy_carrier


class TestCreateEnergyDemands:
    id_product = 1
    electricity_demand_in_gj_per_ton = 100

    @patch.object(EnergyDemand, '__init__', energy_demand_init_mock)
    def test_with_zero_fuel_demand(self, sut):
        sut._create_energy_demand = MagicMock(return_value='dummy_energy_demand')

        id_process = 10
        fuel_demand_in_gj_per_ton = 0
        result = sut.create_energy_demands(
            self.id_product,
            id_process,
            self.electricity_demand_in_gj_per_ton,
            fuel_demand_in_gj_per_ton,
        )

        assert len(result) == 1
        assert result[0].energy_carrier == 'dummy_electricity_energy_carrier'

    @patch.object(EnergyDemand, '__init__', energy_demand_init_mock)
    def test_with_non_zero_fuel_demand(self, sut):
        sut._create_energy_demand = MagicMock(return_value='dummy_energy_demand')

        id_process = 10
        fuel_demand_in_gj_per_ton = 10
        result = sut.create_energy_demands(
            self.id_product,
            id_process,
            self.electricity_demand_in_gj_per_ton,
            fuel_demand_in_gj_per_ton,
        )

        assert result[0].energy_carrier == 'dummy_electricity_energy_carrier'
        assert result[1] == 'dummy_energy_demand'

    @patch.object(EnergyDemand, '__init__', energy_demand_init_mock)
    def test_with_missing_mapping_entry(self, sut):
        sut._create_energy_demand = MagicMock(return_value='dummy_energy_demand')

        id_process = 1000
        fuel_demand_in_gj_per_ton = 10

        with pytest.raises(ValueError, match="'No feedstock shares"):
            sut.create_energy_demands(
                self.id_product,
                id_process,
                self.electricity_demand_in_gj_per_ton,
                fuel_demand_in_gj_per_ton,
            )


@patch.object(EnergyDemand, '__init__', energy_demand_init_mock)
def test_create_energy_demand(sut):
    row = {'id_energy_carrier': 100, 'fuel_share': 0.8}
    fuel_demand_in_gj_per_ton = 100
    result = sut._create_energy_demand(row, fuel_demand_in_gj_per_ton)
    assert result is not None
