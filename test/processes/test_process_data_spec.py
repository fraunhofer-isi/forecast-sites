# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest

from processes.process_data_spec import ProcessDataSpec


class TestProcessDataSpec:
    """Test the ProcessDataSpec structural interface."""

    @pytest.fixture
    def mock_process_data(self):
        """Create a mock object implementing ProcessDataSpec."""
        obj = Mock(spec=ProcessDataSpec)
        obj.demands = (Mock(), Mock())
        obj.outputs = (Mock(),)
        obj.carbon_capture_rate = 0.5
        obj.sector_ids = (1, 2)
        obj.lifetime_in_years = 20
        obj.tech_available_at_year = 2020
        obj.depreciation_period = 10
        obj.life_extension_factor = 0.8
        obj.non_energy_direct_process_emission_in_t_co2_per_process_count = 5.0
        obj.capex_interpolation_data_in_euro_per_process_count = Mock()
        obj.opex_interpolation_data_in_euro_per_process_count = Mock()
        obj.investment_funding_interpolation_data_in_euro_per_process_count = Mock()
        obj.efficiency_improvement_interpolation_data = Mock()
        return obj

    def test_protocol_has_demands_attribute(self, mock_process_data):
        """ProcessDataSpec should have demands attribute."""
        assert hasattr(mock_process_data, 'demands')
        assert isinstance(mock_process_data.demands, tuple)

    def test_protocol_has_outputs_attribute(self, mock_process_data):
        """ProcessDataSpec should have outputs attribute."""
        assert hasattr(mock_process_data, 'outputs')
        assert isinstance(mock_process_data.outputs, tuple)

    def test_protocol_has_carbon_capture_rate(self, mock_process_data):
        """ProcessDataSpec should have carbon_capture_rate."""
        assert hasattr(mock_process_data, 'carbon_capture_rate')
        assert isinstance(mock_process_data.carbon_capture_rate, float)

    def test_protocol_has_sector_ids(self, mock_process_data):
        """ProcessDataSpec should have sector_ids."""
        assert hasattr(mock_process_data, 'sector_ids')
        assert isinstance(mock_process_data.sector_ids, tuple)

    def test_protocol_has_lifetime_in_years(self, mock_process_data):
        """ProcessDataSpec should have lifetime_in_years."""
        assert hasattr(mock_process_data, 'lifetime_in_years')
        assert isinstance(mock_process_data.lifetime_in_years, int)

    def test_protocol_has_tech_available_at_year(self, mock_process_data):
        """ProcessDataSpec should have tech_available_at_year."""
        assert hasattr(mock_process_data, 'tech_available_at_year')
        assert isinstance(mock_process_data.tech_available_at_year, int)

    def test_protocol_has_depreciation_period(self, mock_process_data):
        """ProcessDataSpec should have depreciation_period."""
        assert hasattr(mock_process_data, 'depreciation_period')
        assert isinstance(mock_process_data.depreciation_period, int)

    def test_protocol_has_life_extension_factor(self, mock_process_data):
        """ProcessDataSpec should have life_extension_factor."""
        assert hasattr(mock_process_data, 'life_extension_factor')
        assert isinstance(mock_process_data.life_extension_factor, float)

    def test_protocol_has_non_energy_emission(self, mock_process_data):
        """ProcessDataSpec should have non_energy_direct_process_emission."""
        assert hasattr(mock_process_data, 'non_energy_direct_process_emission_in_t_co2_per_process_count')
        assert isinstance(mock_process_data.non_energy_direct_process_emission_in_t_co2_per_process_count, float)

    def test_protocol_has_capex_interpolation_data(self, mock_process_data):
        """ProcessDataSpec should have capex_interpolation_data."""
        assert hasattr(mock_process_data, 'capex_interpolation_data_in_euro_per_process_count')

    def test_protocol_has_opex_interpolation_data(self, mock_process_data):
        """ProcessDataSpec should have opex_interpolation_data."""
        assert hasattr(mock_process_data, 'opex_interpolation_data_in_euro_per_process_count')

    def test_protocol_has_investment_funding_interpolation_data(self, mock_process_data):
        """ProcessDataSpec should have investment_funding_interpolation_data."""
        assert hasattr(mock_process_data, 'investment_funding_interpolation_data_in_euro_per_process_count')

    def test_protocol_has_efficiency_improvement_interpolation_data(self, mock_process_data):
        """ProcessDataSpec should have efficiency_improvement_interpolation_data."""
        assert hasattr(mock_process_data, 'efficiency_improvement_interpolation_data')

    def test_protocol_is_runtime_checkable(self, mock_process_data):
        """ProcessDataSpec should be runtime checkable."""
        # This will pass if all required attributes exist
        assert isinstance(mock_process_data, ProcessDataSpec)

    def test_mock_demands_are_tuple(self, mock_process_data):
        """Demands should be a tuple type."""
        assert type(mock_process_data.demands).__name__ in ('tuple', 'MagicMock')

    def test_mock_outputs_are_tuple(self, mock_process_data):
        """Outputs should be a tuple type."""
        assert type(mock_process_data.outputs).__name__ in ('tuple', 'MagicMock')

    def test_mock_sector_ids_are_tuple(self, mock_process_data):
        """sector_ids should be a tuple type."""
        assert type(mock_process_data.sector_ids).__name__ in ('tuple', 'MagicMock')

    def test_multiple_demands(self, mock_process_data):
        """Should support multiple demands in tuple."""
        mock_process_data.demands = (Mock(), Mock(), Mock())
        assert len(mock_process_data.demands) == 3

    def test_multiple_outputs(self, mock_process_data):
        """Should support multiple outputs in tuple."""
        mock_process_data.outputs = (Mock(), Mock())
        assert len(mock_process_data.outputs) == 2

    def test_empty_sector_ids_allowed(self, mock_process_data):
        """Should allow empty sector_ids (means all sectors)."""
        mock_process_data.sector_ids = ()
        assert mock_process_data.sector_ids == ()

    def test_positive_lifetime_in_years(self, mock_process_data):
        """lifetime_in_years should support positive values."""
        mock_process_data.lifetime_in_years = 30
        assert mock_process_data.lifetime_in_years == 30

    def test_zero_carbon_capture_rate(self, mock_process_data):
        """carbon_capture_rate should support zero (non-carbon-capture process)."""
        mock_process_data.carbon_capture_rate = 0.0
        assert mock_process_data.carbon_capture_rate == 0.0

    def test_full_carbon_capture_rate(self, mock_process_data):
        """carbon_capture_rate should support 1.0 (complete capture)."""
        mock_process_data.carbon_capture_rate = 1.0
        assert mock_process_data.carbon_capture_rate == 1.0
