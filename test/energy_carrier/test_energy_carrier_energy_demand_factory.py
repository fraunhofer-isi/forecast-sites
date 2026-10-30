# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pandas as pd
import pytest

from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand
from energy_carrier.energy_carrier_energy_demand_factory import (
    EnergyCarrierEnergyDemandFactory,
)


class TestEnergyCarrierEnergyDemandFactory:
    """Test the EnergyCarrierEnergyDemandFactory class."""

    @pytest.fixture
    def mock_energy_carrier_demand_data(self):
        """Create mock energy carrier demand data."""
        return pd.DataFrame(
            {
                'id_process': [1, 1, 2, 2],
                'id_energy_carrier': [1, 2, 1, 3],
                'demand_in_gj_per_process_count': [500.0, 250.0, 1000.0, 150.0],
            }
        ).set_index('id_process')

    @pytest.fixture
    def mock_energy_carriers(self):
        """Create mock energy carriers map with electricity at id=1."""
        return {
            1: Mock(id=1, name='Electricity'),
            2: Mock(id=2, name='Natural Gas'),
            3: Mock(id=3, name='Heat'),
        }

    @pytest.fixture
    def mock_efficiency_data(self):
        """Create mock efficiency improvement data."""
        return Mock(value_for_start_year=1.0, value_for_end_year=0.95)

    @pytest.fixture
    def mock_simulation_options(self):
        """Create mock simulation options."""
        return {'start_year': 2020, 'end_year': 2030}

    def test_factory_initialization(
        self, mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
    ):
        """Should initialize with all required parameters."""
        factory = EnergyCarrierEnergyDemandFactory(
            mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
        )
        assert factory is not None
        assert factory._carriers == mock_energy_carriers
        assert factory._efficiency_improvement_interpolation_data == mock_efficiency_data
        assert factory._simulation_options == mock_simulation_options

    def test_electricity_reference_initialized(
        self, mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
    ):
        """Should initialize electricity reference (id=1) for optimization."""
        factory = EnergyCarrierEnergyDemandFactory(
            mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
        )
        assert factory.electricity == mock_energy_carriers[1]
        assert factory.electricity.id == 1

    def test_create_returns_list_of_demands(
        self, mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
    ):
        """create() should return a list of EnergyCarrierEnergyDemand objects."""
        factory = EnergyCarrierEnergyDemandFactory(
            mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
        )
        demands = factory.create(1)

        assert isinstance(demands, list)
        assert len(demands) == 2
        assert all(isinstance(d, EnergyCarrierEnergyDemand) for d in demands)

    def test_create_returns_correct_demands_for_process(
        self, mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
    ):
        """Should return only demands for specified process."""
        factory = EnergyCarrierEnergyDemandFactory(
            mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
        )

        demands_process_1 = factory.create(1)
        demands_process_2 = factory.create(2)

        assert len(demands_process_1) == 2
        assert len(demands_process_2) == 2

    def test_demand_object_creation(
        self, mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
    ):
        """Should create EnergyCarrierEnergyDemand with correct attributes."""
        factory = EnergyCarrierEnergyDemandFactory(
            mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
        )

        demands = factory.create(1)
        first_demand = demands[0]

        assert first_demand._raw_demand_in_gj_per_process_count == 500.0
        assert first_demand.energy_carrier == mock_energy_carriers[1]
        assert first_demand._simulation_options == mock_simulation_options

    def test_create_empty_when_no_matching_process(
        self, mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
    ):
        """Should return empty list when process ID doesn't exist."""
        factory = EnergyCarrierEnergyDemandFactory(
            mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
        )

        demands = factory.create(999)
        assert demands == []

    def test_demand_inherits_from_base_class(
        self, mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
    ):
        """EnergyCarrierEnergyDemandFactory should inherit from DemandFactory."""
        from demand.demand_factory import DemandFactory

        factory = EnergyCarrierEnergyDemandFactory(
            mock_energy_carrier_demand_data, mock_energy_carriers, mock_efficiency_data, mock_simulation_options
        )
        assert isinstance(factory, DemandFactory)
