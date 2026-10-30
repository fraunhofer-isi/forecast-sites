# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest

from by_product.by_product_output import ByProductOutput


class TestByProductOutput:
    """Test the ByProductOutput class."""

    @pytest.fixture
    def mock_by_product(self):
        """Create mock by-product."""
        mock = Mock()
        mock.sell_price_in_euro_per_t.return_value = 100.0
        mock.downstream_emission_in_t_co2_per_unit.return_value = 0.2
        mock.renewably_bound_co2_emission_in_t_co2_per_unit.return_value = 0.05
        mock.__str__ = Mock(return_value='Steel Scrap')
        return mock

    def test_initialization(self, mock_by_product):
        """Should initialize with by-product and output amount."""
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)
        assert output.output_in_t_per_process_count == 50.0
        assert output.carrier == mock_by_product

    def test_by_product_property(self, mock_by_product):
        """Should return by_product via carrier property."""
        output = ByProductOutput(mock_by_product, 50.0)
        assert output.by_product == mock_by_product

    def test_repr(self, mock_by_product):
        """Should provide clear string representation."""
        output = ByProductOutput(mock_by_product, 50.0)
        repr_str = repr(output)
        assert 'ByProductOutput' in repr_str
        assert '50.0' in repr_str

    def test_output_in_euro_per_process_count(self, mock_by_product):
        """Should calculate output value in euros accounting for downstream emissions."""
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)
        # Price: 100, downstream emission: 0.2, CO2 price: 50
        # Emission adjusted price: 100 - 0.2 * 50 = 100 - 10 = 90
        # Output value: 50 * 90 = 4500
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 4500.0

    def test_output_in_euro_zero_emissions(self, mock_by_product):
        """Should use full price when by-product has zero downstream emissions."""
        mock_by_product.downstream_emission_in_t_co2_per_unit.return_value = 0.0
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 5000.0  # 50 * 100

    def test_output_in_euro_high_emissions(self, mock_by_product):
        """Should reduce price significantly with high downstream emissions."""
        mock_by_product.downstream_emission_in_t_co2_per_unit.return_value = 2.0
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)
        # Price: 100, downstream: 2.0, CO2 price: 50
        # Adjusted price: 100 - 2.0 * 50 = 0
        value = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        assert value == 0.0

    def test_output_in_euro_price_varies_by_year(self, mock_by_product):
        """Should use different prices for different years."""
        mock_by_product.sell_price_in_euro_per_t.side_effect = [100.0, 110.0]
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)

        value_2025 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=50.0, simulation_options={})
        value_2026 = output.output_in_euro_per_process_count(2026, co2_price_in_euro_per_t_co2=50.0, simulation_options={})

        # 2025: (100 - 0.2*50) * 50 = 4500
        # 2026: (110 - 0.2*50) * 50 = 5000
        assert value_2025 == 4500.0
        assert value_2026 == 5000.0

    def test_output_in_t_scaling(self, mock_by_product):
        """Should scale output by execution count."""
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)
        total_output = output.output_in_t(execution_count=10)
        assert total_output == 500.0  # 50 * 10

    def test_output_in_t_zero_execution(self, mock_by_product):
        """Should return 0 when execution count is 0."""
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)
        total_output = output.output_in_t(execution_count=0)
        assert total_output == 0.0

    def test_output_in_euro_scales_with_co2_price(self, mock_by_product):
        """Should scale emission cost adjustment with CO2 price."""
        output = ByProductOutput(mock_by_product, output_in_t_per_process_count=50.0)

        value_low_co2 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=10.0, simulation_options={})
        value_high_co2 = output.output_in_euro_per_process_count(2025, co2_price_in_euro_per_t_co2=100.0, simulation_options={})

        # Low CO2: (100 - 0.2*10) * 50 = 98 * 50 = 4900
        # High CO2: (100 - 0.2*100) * 50 = 80 * 50 = 4000
        assert value_low_co2 == 4900.0
        assert value_high_co2 == 4000.0
        # Higher CO2 price reduces value
        assert value_high_co2 < value_low_co2
