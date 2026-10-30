# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest

from product.product_output import ProductOutput


class TestProductOutput:
    """Test the ProductOutput class."""

    @pytest.fixture
    def mock_product(self):
        """Create mock product."""
        mock = Mock()
        mock.sell_price_in_euro_per_t.return_value = 200.0
        mock.downstream_emission_in_t_co2_per_unit.return_value = 0.3
        mock.__str__ = Mock(return_value='Steel')
        return mock

    def test_initialization(self, mock_product):
        """Should initialize with product and output amount."""
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)
        assert output.output_in_t_per_process_count == 100.0
        assert output.carrier == mock_product

    def test_product_property(self, mock_product):
        """Should return product via carrier property."""
        output = ProductOutput(mock_product, 100.0)
        assert output.product == mock_product

    def test_repr(self, mock_product):
        """Should provide clear string representation."""
        output = ProductOutput(mock_product, 100.0)
        repr_str = repr(output)
        assert 'ProductOutput' in repr_str
        assert '100.0' in repr_str

    def test_output_in_euro_per_process_count(self, mock_product):
        """Should calculate output value in euros accounting for downstream emissions."""
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)
        # Price: 200, downstream emission: 0.3, CO2 price: 50
        # Emission adjusted price: 200 - 0.3 * 50 = 200 - 15 = 185
        # Output value: 100 * 185 = 18500
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 18500.0

    def test_output_in_euro_zero_emissions(self, mock_product):
        """Should use full price when product has zero downstream emissions."""
        mock_product.downstream_emission_in_t_co2_per_unit.return_value = 0.0
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 20000.0  # 100 * 200

    def test_output_in_euro_high_emissions(self, mock_product):
        """Should reduce price with high downstream emissions."""
        mock_product.downstream_emission_in_t_co2_per_unit.return_value = 1.0
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)
        # Price: 200, downstream: 1.0, CO2 price: 50
        # Adjusted price: 200 - 1.0 * 50 = 150
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 15000.0  # 100 * 150

    def test_output_in_euro_price_varies_by_year(self, mock_product):
        """Should use different prices for different years."""
        mock_product.sell_price_in_euro_per_t.side_effect = [200.0, 220.0]
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)

        value_2025 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        value_2026 = output.output_in_euro_per_process_count(2026, co2_price_in_euro_per_t_co2=50.0, simulation_options={})

        # 2025: (200 - 0.3*50) * 100 = 185 * 100 = 18500
        # 2026: (220 - 0.3*50) * 100 = 205 * 100 = 20500
        assert value_2025 == 18500.0
        assert value_2026 == 20500.0

    def test_output_in_t_scaling(self, mock_product):
        """Should scale output by execution count."""
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)
        total_output = output.output_in_t(execution_count=20)
        assert total_output == 2000.0  # 100 * 20

    def test_output_in_t_zero_execution(self, mock_product):
        """Should return 0 when execution count is 0."""
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)
        total_output = output.output_in_t(execution_count=0)
        assert total_output == 0.0

    def test_output_in_euro_scales_with_co2_price(self, mock_product):
        """Should scale emission cost adjustment with CO2 price."""
        output = ProductOutput(mock_product, output_in_t_per_process_count=100.0)

        value_low_co2 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=20.0, simulation_options={})
        value_high_co2 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=100.0, simulation_options={})

        # Low CO2: (200 - 0.3*20) * 100 = 194 * 100 = 19400
        # High CO2: (200 - 0.3*100) * 100 = 170 * 100 = 17000
        assert value_low_co2 == 19400.0
        assert value_high_co2 == 17000.0
        # Higher CO2 price reduces value
        assert value_high_co2 < value_low_co2
