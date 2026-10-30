# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

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
    data_interface.energy_carrier_data = pd.DataFrame(
        [
            {
                'id': 1,
                'name': 'mocked_energy_carrier',
            }
        ]
    )

    data_interface.energy_carrier_purchase_price = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                '2015': 10,
                '2016': 20,
            }
        ],
    ).set_index('id_energy_carrier')

    data_interface.energy_carrier_sell_price = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                '2015': 1,
                '2016': 2,
            }
        ]
    ).set_index('id_energy_carrier')

    data_interface.energy_carrier_availability = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                'availability_start_year_in_gj': 1,
                'availability_end_year_in_gj': 2,
            }
        ]
    ).set_index('id_energy_carrier')

    data_interface.energy_carrier_minimum_use = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                'minimum_use_start_year_in_gj': 1,
                'minimum_use_end_year_in_gj': 2,
            }
        ]
    ).set_index('id_energy_carrier')

    data_interface.energy_carrier_emission = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                'direct_emission_in_t_co2_per_gj': 1,
                'upstream_emission_start_year_in_t_co2_per_gj': 2,
                'upstream_emission_end_year_in_t_co2_per_gj': 3,
                'renewably_bound_co2_emission_in_t_co2_per_gj': 0.0,
            }
        ]
    ).set_index('id_energy_carrier')

    data_interface.energy_carrier_subsidies = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                'subsidies_start_year_in_euro_per_gj': 1,
                'subsidies_interim_year_in_euro_per_gj': 1,
                'subsidies_end_year_in_euro_per_gj': 2,
            }
        ]
    ).set_index('id_energy_carrier')

    data_interface.energy_carrier_taxes = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                'taxes_start_year_in_euro_per_gj': 1,
                'taxes_end_year_in_euro_per_gj': 2,
            }
        ]
    ).set_index('id_energy_carrier')

    data_interface.energy_carrier_maximum_production = pd.DataFrame(
        [
            {
                'id_energy_carrier': 1,
                'maximum_production_in_gj': 100,
            }
        ]
    ).set_index('id_energy_carrier')

    energy_carrier_factory = EnergyCarrierFactory(data_interface)
    return energy_carrier_factory


def energy_carrier_init_mock(
    self,
    id_energy_carrier,
    name,
    data,
):
    self.name = name
    self.id_energy_carrier = id_energy_carrier
    self.data = data


def test_construction(sut):
    assert sut is not None


def test_create_map(sut):
    sut._energy_carrier = MagicMock(return_value='dummy_energy_carrier')
    result = sut.create_map()
    assert isinstance(result, dict)

    energy_carrier = result[1]
    assert energy_carrier == 'dummy_energy_carrier'


@patch.object(EnergyCarrier, '__init__', energy_carrier_init_mock)
def test_energy_carrier(sut):
    id_energy_carrier = 1
    name = 'dummy'
    result = sut._energy_carrier(id_energy_carrier, name)
    assert isinstance(result, EnergyCarrier)
    assert result.name == name
