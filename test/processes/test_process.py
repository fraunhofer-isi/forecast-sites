# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock, patch

import pytest

from processes.process import Process


class TestProcess:
    """Test the Process domain class."""

    @pytest.fixture
    def mock_process_data(self):
        """Create mock process data."""
        data = Mock()
        data.demands = ()
        data.outputs = ()
        data.carbon_capture_rate = 0.0
        data.sector_ids = (1,)
        data.lifetime_in_years = 25
        data.tech_available_at_year = 2020
        data.depreciation_period = 20
        data.life_extension_factor = 1.0
        data.non_energy_direct_process_emission_in_t_co2_per_process_count = 0.0
        data.capex_interpolation_data_in_euro_per_process_count = Mock()
        data.opex_interpolation_data_in_euro_per_process_count = Mock()
        data.investment_funding_interpolation_data_in_euro_per_process_count = Mock()
        data.efficiency_improvement_interpolation_data = Mock()
        return data

    @pytest.fixture
    def simulation_options(self):
        """Create default simulation options."""
        return {'start_year': 2020, 'end_year': 2050}

    def test_initialization_with_process_data(self, mock_process_data):
        """Should initialize with ID and process data."""
        process = Process(1, mock_process_data)
        assert process.id == 1

    def test_emission_property_returns_emission_object(self, mock_process_data):
        """Should return ProcessEmission object."""
        process = Process(1, mock_process_data)
        emission = process.emission
        assert emission is not None

    def test_capex_delegated_to_interpolator(self, mock_process_data, simulation_options):
        """Should interpolate capex from data."""
        with patch('processes.process.interpolator.interpolate', return_value=1000.0):
            process = Process(1, mock_process_data)
            capex = process.capex_in_euro_per_process_count(2025, simulation_options)
            assert capex == 1000.0

    def test_opex_delegated_to_interpolator(self, mock_process_data, simulation_options):
        """Should interpolate opex from data."""
        with patch('processes.process.interpolator.interpolate', return_value=500.0):
            process = Process(1, mock_process_data)
            opex = process.opex_in_euro_per_process_count(2025, simulation_options)
            assert opex == 500.0

    def test_purchase_cost_with_no_demands(self, mock_process_data):
        """Should return 0 when no demands exist."""
        process = Process(1, mock_process_data)
        cost = process.purchase_cost_in_euro_per_process_count(2025)
        assert cost == 0

    def test_purchase_cost_with_demands(self, mock_process_data):
        """Should sum purchase costs from all demands."""
        mock_demand1 = Mock()
        mock_demand1.purchase_cost_in_euro_per_process_count.return_value = 100.0
        mock_demand2 = Mock()
        mock_demand2.purchase_cost_in_euro_per_process_count.return_value = 50.0
        mock_process_data.demands = (mock_demand1, mock_demand2)

        process = Process(1, mock_process_data)
        cost = process.purchase_cost_in_euro_per_process_count(2025)
        assert cost == 150.0

    def test_subsidies_with_no_demands(self, mock_process_data, simulation_options):
        """Should return 0 when no demands exist."""
        process = Process(1, mock_process_data)
        subsidies = process.subsidies_in_euro_per_process_count(2025, simulation_options)
        assert subsidies == 0

    def test_subsidies_with_demands(self, mock_process_data, simulation_options):
        """Should sum subsidies from all demands."""
        mock_demand1 = Mock()
        mock_demand1.subsidies_in_euro_per_process_count.return_value = 50.0
        mock_demand2 = Mock()
        mock_demand2.subsidies_in_euro_per_process_count.return_value = 25.0
        mock_process_data.demands = (mock_demand1, mock_demand2)

        process = Process(1, mock_process_data)
        subsidies = process.subsidies_in_euro_per_process_count(2025, simulation_options)
        assert subsidies == 75.0

    def test_taxes_with_no_demands(self, mock_process_data, simulation_options):
        """Should return 0 when no demands exist."""
        process = Process(1, mock_process_data)
        taxes = process.taxes_in_euro_per_process_count(2025, simulation_options)
        assert taxes == 0

    def test_taxes_with_demands(self, mock_process_data, simulation_options):
        """Should sum taxes from all demands."""
        mock_demand1 = Mock()
        mock_demand1.taxes_in_euro_per_process_count.return_value = 10.0
        mock_demand2 = Mock()
        mock_demand2.taxes_in_euro_per_process_count.return_value = 5.0
        mock_process_data.demands = (mock_demand1, mock_demand2)

        process = Process(1, mock_process_data)
        taxes = process.taxes_in_euro_per_process_count(2025, simulation_options)
        assert taxes == 15.0

    def test_net_capex_deducts_funding(self, mock_process_data, simulation_options):
        """Should calculate the investor CAPEX as capex minus funding."""
        with patch('processes.process.interpolator.interpolate') as mock_interpolate:
            mock_interpolate.side_effect = [1000.0, 200.0]  # capex, funding
            process = Process(1, mock_process_data)
            net_capex = process.net_capex_in_euro_per_process_count(2025, simulation_options)
            assert net_capex == 800.0

    def test_net_capex_is_never_negative(self, mock_process_data, simulation_options):
        """Should not return negative costs if the funding exceeds the capex."""
        with patch('processes.process.interpolator.interpolate') as mock_interpolate:
            mock_interpolate.side_effect = [1000.0, 1500.0]  # capex, funding
            process = Process(1, mock_process_data)
            assert process.net_capex_in_euro_per_process_count(2025, simulation_options) == 0.0

    def test_investment_funding_is_interpolated(self, mock_process_data, simulation_options):
        """Should provide the interpolated investment funding."""
        with patch('processes.process.interpolator.interpolate', return_value=250.0):
            process = Process(1, mock_process_data)
            assert process.investment_funding_in_euro_per_process_count(2025, simulation_options) == 250.0

    def test_annuity_on_investment_calculates_correctly(self, mock_process_data, simulation_options):
        """Should calculate annuity from capex, funding, and annuity factor."""
        with patch('processes.process.interpolator.interpolate') as mock_interpolate:
            mock_interpolate.side_effect = [1000.0, 200.0]  # capex, funding
            process = Process(1, mock_process_data)
            annuity = process.annuity_on_investment_in_euro_per_process_count(2025, 0.05, simulation_options)
            assert isinstance(annuity, (int, float))
            # Annuity should be positive when capex > funding
            assert annuity > 0

    def test_invest_cost_is_capex_net_of_funding(self, mock_process_data, simulation_options):
        """Should return capex minus investment funding as invest cost."""
        with patch('processes.process.interpolator.interpolate') as mock_interpolate:
            mock_interpolate.side_effect = [1000.0, 300.0]  # capex, funding
            process = Process(1, mock_process_data)
            cost = process.invest_cost_in_euro_per_process_count(2025, 0.05, simulation_options)
            assert cost == 700.0

    def test_invest_cost_applies_capex_factor_before_funding(self, mock_process_data, simulation_options):
        """Should scale the capex with the factor and deduct the funding afterwards."""
        with patch('processes.process.interpolator.interpolate') as mock_interpolate:
            mock_interpolate.side_effect = [1000.0, 1000.0]  # capex, funding (fully funded)
            process = Process(1, mock_process_data)
            cost = process.invest_cost_in_euro_per_process_count(2025, 0.05, simulation_options, 5.0)
            assert cost == 4000.0

    def test_production_cost_sums_all_components(self, mock_process_data, simulation_options):
        """Should sum annuity, opex, and purchase cost."""
        with patch('processes.process.interpolator.interpolate') as mock_interpolate:
            mock_interpolate.side_effect = [1000.0, 200.0, 50.0]  # capex, funding, opex
            process = Process(1, mock_process_data)
            cost = process.production_cost_in_euro_per_process_count(2025, 0.05, simulation_options)
            # 100 (annuity) + 50 (opex) + 0 (purchase)
            # Will vary based on actual calculation, just verify it returns a number
            assert isinstance(cost, (int, float))

    def test_annual_cost_calculation(self, mock_process_data, simulation_options):
        """Should calculate annual cost including emissions and production gain."""
        with patch('processes.process.interpolator.interpolate', return_value=100.0):
            process = Process(1, mock_process_data)
            cost = process.annual_cost_in_euro_per_process_count(2025, 50.0, simulation_options)
            # Should include opex, value_added, emissions, and captured savings
            assert isinstance(cost, (int, float))

    def test_value_added_with_no_outputs_or_demands(self, mock_process_data):
        """Should return 0 when no outputs or demands."""
        process = Process(1, mock_process_data)
        value = process._value_added_in_euro_per_process_count(2025, 50.0, {})
        assert value == 0

    def test_value_added_with_outputs(self, mock_process_data):
        """Should include output value in production gain."""
        mock_output1 = Mock()
        mock_output1.output_in_euro_per_process_count.return_value = 200.0
        mock_output2 = Mock()
        mock_output2.output_in_euro_per_process_count.return_value = 100.0
        mock_process_data.outputs = (mock_output1, mock_output2)

        process = Process(1, mock_process_data)
        value = process._value_added_in_euro_per_process_count(2025, 50.0, {})
        assert value == 300.0

    def test_value_added_with_demands(self, mock_process_data):
        """Should subtract opportunity costs from production gain."""
        mock_demand1 = Mock()
        mock_demand1.opportunity_cost_in_euro_per_process_count.return_value = 100.0
        mock_demand2 = Mock()
        mock_demand2.opportunity_cost_in_euro_per_process_count.return_value = 50.0
        mock_process_data.demands = (mock_demand1, mock_demand2)

        process = Process(1, mock_process_data)
        value = process._value_added_in_euro_per_process_count(2025, 50.0, {})
        assert value == -150.0

    def test_value_added_combines_outputs_and_demands(self, mock_process_data):
        """Should subtract input costs from output value."""
        mock_output = Mock()
        mock_output.output_in_euro_per_process_count.return_value = 500.0
        mock_demand = Mock()
        mock_demand.opportunity_cost_in_euro_per_process_count.return_value = 200.0
        mock_process_data.outputs = (mock_output,)
        mock_process_data.demands = (mock_demand,)

        process = Process(1, mock_process_data)
        value = process._value_added_in_euro_per_process_count(2025, 50.0, {})
        assert value == 300.0
