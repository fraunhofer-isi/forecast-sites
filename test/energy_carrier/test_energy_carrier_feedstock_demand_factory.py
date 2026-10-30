# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from pandas import Series
from test_utils.isi_mock import Mock

from energy_carrier.energy_carrier_feedstock_demand import EnergyCarrierFeedstockDemand
from energy_carrier.energy_carrier_feedstock_demand_factory import (
    EnergyCarrierFeedstockDemandFactory,
)
from interpolation.interpolation_data import InterpolationData

energy_carrier = Mock()

efficiency_improvement_interpolation_data = InterpolationData(0, 0)
simulation_options = {
    'start_year': 2000,
    'interim_year': 2025,
    'end_year': 2050,
}


@pytest.fixture
def sut():
    process_energy_carrier_feedstock_demand = Mock()
    energy_carriers = {1: energy_carrier}
    return EnergyCarrierFeedstockDemandFactory(
        process_energy_carrier_feedstock_demand,
        energy_carriers,
        efficiency_improvement_interpolation_data,
        simulation_options,
    )


def test_demand(sut):
    row = Series({'demand_in_gj_per_process_count': 42}, name=1)
    result = sut._demand(row)

    assert isinstance(result, EnergyCarrierFeedstockDemand)
    assert result.energy_carrier == energy_carrier
    year = 2000
    assert result.demand_in_gj_per_process_count(year) == 42
