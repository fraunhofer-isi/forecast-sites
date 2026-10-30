# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock, patch

import pytest

from energy_carrier.energy_carrier_energy_demand import EnergyCarrierEnergyDemand


class TestEnergyCarrierEnergyDemand:
    """Test the EnergyCarrierEnergyDemand class."""

    @pytest.fixture
    def mock_energy_carrier(self):
        """Create mock energy carrier."""
        mock = Mock()
        mock.direct_emission_in_t_co2_per_gj = 0.1
        mock.purchase_price_in_euro_per_gj.return_value = 20.0
        mock.sell_price_in_euro_per_gj.return_value = 25.0
        mock.subsidies_in_euro_per_gj.return_value = 2.0
        mock.taxes_in_euro_per_gj.return_value = 1.0
        mock.downstream_emission_in_t_co2_per_unit.return_value = 0.05
        return mock

    @pytest.fixture
    def mock_efficiency_data(self):
        """Create mock efficiency improvement data."""
        return Mock()

    @pytest.fixture
    def simulation_options(self):
        """Create default simulation options."""
        return {'start_year': 2020}

    def test_initialization(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should initialize with energy carrier, demand, and efficiency data."""
        demand = EnergyCarrierEnergyDemand(
            mock_energy_carrier,
            demand_in_gj_per_process_count=500.0,
            efficiency_improvement_interpolation_data=mock_efficiency_data,
            simulation_options=simulation_options,
        )
        assert demand._raw_demand_in_gj_per_process_count == 500.0
        assert demand.carrier == mock_energy_carrier

    def test_energy_carrier_property(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should return energy_carrier via carrier property."""
        demand = EnergyCarrierEnergyDemand(mock_energy_carrier, 500.0, mock_efficiency_data, simulation_options)
        assert demand.energy_carrier == mock_energy_carrier

    def test_demand_in_gj_per_process_count_with_efficiency(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should apply efficiency factor to raw demand."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=0.9):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            result = demand.demand_in_gj_per_process_count(2025)
            assert result == 450.0  # 500 * 0.9

    def test_demand_in_gj_full_scaling(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should scale demand by process execution count and efficiency."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            total_demand = demand.demand_in_gj(2025, process_execution_count=10)
            assert total_demand == 5000.0  # 500 * 1.0 * 10

    def test_purchase_cost_is_raw_cost_only(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should return the raw purchase cost only."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            cost = demand.purchase_cost_in_euro_per_process_count(2025)
            # Raw cost: 500 * 20 = 10000
            assert cost == 10000.0

    def test_raw_purchase_cost(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should calculate raw purchase cost as demand * price."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            raw_cost = demand._raw_purchase_cost_in_euro_per_process_count(2025)
            assert raw_cost == 10000.0  # 500 * 20

    def test_direct_emission_per_process_count(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should calculate direct emissions as demand * emission_per_gj."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            emission = demand.direct_emission_in_t_co2_per_process_count(2025)
            assert emission == 50.0  # 500 * 0.1

    def test_direct_emission_total(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should scale direct emissions by process execution count."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            emission = demand.direct_emission_in_t_co2(2025, process_execution_count=10)
            assert emission == 500.0  # 50 * 10

    def test_opportunity_cost_with_downstream_emissions(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should account for downstream emissions in opportunity cost."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            cost = demand.opportunity_cost_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0)
            # Sell price: 25, downstream emission: 0.05
            # Emission adjusted price: 25 - 0.05 * 50 = 25 - 2.5 = 22.5
            # Cost: 500 * 22.5 = 11250
            assert cost == 11250.0

    def test_direct_emission_cost(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should calculate direct emission cost."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            cost = demand.direct_emission_cost_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0)
            assert cost == 2500.0  # 50 t_co2 * 50 euro/t_co2

    def test_subsidies_calculation(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should calculate total subsidies as demand * subsidy_per_gj."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            subsidies = demand.subsidies_in_euro_per_process_count(2025, simulation_options)
            assert subsidies == 1000.0  # 500 * 2

    def test_taxes_calculation(self, mock_energy_carrier, mock_efficiency_data, simulation_options):
        """Should calculate total taxes as demand * tax_per_gj."""
        with patch.object(EnergyCarrierEnergyDemand, '_efficiency_factor', return_value=1.0):
            demand = EnergyCarrierEnergyDemand(
                mock_energy_carrier,
                demand_in_gj_per_process_count=500.0,
                efficiency_improvement_interpolation_data=mock_efficiency_data,
                simulation_options=simulation_options,
            )
            taxes = demand.taxes_in_euro_per_process_count(2025, simulation_options)
            assert taxes == 500.0  # 500 * 1
