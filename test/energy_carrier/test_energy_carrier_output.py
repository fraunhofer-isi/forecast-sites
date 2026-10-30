# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest

from energy_carrier.energy_carrier_output import EnergyCarrierOutput


class TestEnergyCarrierOutput:
    """Test the EnergyCarrierOutput class."""

    @pytest.fixture
    def mock_energy_carrier(self):
        """Create mock energy carrier."""
        mock = Mock()
        mock.sell_price_in_euro_per_gj.return_value = 30.0
        mock.downstream_emission_in_t_co2_per_unit.return_value = 0.1
        mock.__str__ = Mock(return_value='Electricity')
        return mock

    def test_initialization(self, mock_energy_carrier):
        """Should initialize with energy carrier and output amount."""
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)
        assert output.output_in_gj_per_process_count == 200.0
        assert output.carrier == mock_energy_carrier

    def test_energy_carrier_property(self, mock_energy_carrier):
        """Should return energy_carrier via carrier property."""
        output = EnergyCarrierOutput(mock_energy_carrier, 200.0)
        assert output.energy_carrier == mock_energy_carrier

    def test_repr(self, mock_energy_carrier):
        """Should provide clear string representation."""
        output = EnergyCarrierOutput(mock_energy_carrier, 200.0)
        repr_str = repr(output)
        assert 'EnergyCarrierOutput' in repr_str
        assert '200.0' in repr_str

    def test_output_in_euro_per_process_count(self, mock_energy_carrier):
        """Should calculate output value in euros accounting for downstream emissions."""
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)
        # Price: 30, downstream emission: 0.1, CO2 price: 50
        # Emission adjusted price: 30 - 0.1 * 50 = 30 - 5 = 25
        # Output value: 200 * 25 = 5000
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 5000.0

    def test_output_in_euro_zero_emissions(self, mock_energy_carrier):
        """Should use full price when energy carrier has zero downstream emissions."""
        mock_energy_carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.0
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 6000.0  # 200 * 30

    def test_output_in_euro_high_emissions(self, mock_energy_carrier):
        """Should reduce price with high downstream emissions."""
        mock_energy_carrier.downstream_emission_in_t_co2_per_unit.return_value = 0.5
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)
        # Price: 30, downstream: 0.5, CO2 price: 50
        # Adjusted price: 30 - 0.5 * 50 = 5
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 1000.0  # 200 * 5

    def test_output_in_euro_price_varies_by_year(self, mock_energy_carrier):
        """Should use different prices for different years."""
        mock_energy_carrier.sell_price_in_euro_per_gj.side_effect = [30.0, 35.0]
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)

        value_2025 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        value_2026 = output.output_in_euro_per_process_count(2026, co2_price_in_euro_per_t_co2=50.0, simulation_options={})

        # 2025: (30 - 0.1*50) * 200 = 25 * 200 = 5000
        # 2026: (35 - 0.1*50) * 200 = 30 * 200 = 6000
        assert value_2025 == 5000.0
        assert value_2026 == 6000.0

    def test_output_in_gj_scaling(self, mock_energy_carrier):
        """Should scale output by execution count."""
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)
        total_output = output.output_in_gj(execution_count=5)
        assert total_output == 1000.0  # 200 * 5

    def test_output_in_gj_zero_execution(self, mock_energy_carrier):
        """Should return 0 when execution count is 0."""
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)
        total_output = output.output_in_gj(execution_count=0)
        assert total_output == 0.0

    def test_output_in_euro_scales_with_co2_price(self, mock_energy_carrier):
        """Should scale emission cost adjustment with CO2 price."""
        output = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)

        value_low_co2 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=10.0, simulation_options={})
        value_high_co2 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=100.0, simulation_options={})

        # Low CO2: (30 - 0.1*10) * 200 = 29 * 200 = 5800
        # High CO2: (30 - 0.1*100) * 200 = 20 * 200 = 4000
        assert value_low_co2 == 5800.0
        assert value_high_co2 == 4000.0
        # Higher CO2 price reduces value
        assert value_high_co2 < value_low_co2

    def test_output_scales_linearly_with_output_amount(self, mock_energy_carrier):
        """Should scale output value linearly with output amount per process."""
        output1 = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=100.0)
        output2 = EnergyCarrierOutput(mock_energy_carrier, output_in_gj_per_process_count=200.0)

        value1 = output1.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        value2 = output2.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})

        # Value2 should be exactly 2x Value1
        assert value2 == 2 * value1
