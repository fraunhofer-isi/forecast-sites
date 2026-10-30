# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest

from carrier.carrier_unit import CarrierUnit
from processes.abstract_process import AbstractProcess


class TestAbstractProcess:
    """Test the AbstractProcess base class."""

    @pytest.fixture
    def mock_process_data(self):
        """Create mock process data."""
        data = Mock()
        data.demands = (Mock(carrier=Mock(unit=CarrierUnit.GJ)),)
        data.outputs = (Mock(carrier=Mock(unit=CarrierUnit.T)),)
        data.carbon_capture_rate = 0.5
        data.sector_ids = (1, 2)
        data.lifetime_in_years = 25
        data.tech_available_at_year = 2020
        data.depreciation_period = 20
        data.life_extension_factor = 1.2
        data.non_energy_direct_process_emission_in_t_co2_per_process_count = 5.0
        data.capex_interpolation_data_in_euro_per_process_count = Mock()
        data.opex_interpolation_data_in_euro_per_process_count = Mock()
        data.investment_funding_interpolation_data_in_euro_per_process_count = Mock()
        data.efficiency_improvement_interpolation_data = Mock()
        return data

    def test_initialization(self, mock_process_data):
        """Should initialize with process ID and data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.id == 1

    def test_process_data_must_implement_protocol(self):
        """Should raise TypeError if process_data doesn't implement ProcessDataSpec."""
        invalid_data = Mock(spec=[])  # No attributes

        with pytest.raises(TypeError, match='ProcessDataSpec'):
            AbstractProcess(1, invalid_data)

    def test_demands_delegated_to_data(self, mock_process_data):
        """Should delegate demands to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.demands == mock_process_data.demands

    def test_outputs_delegated_to_data(self, mock_process_data):
        """Should delegate outputs to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.outputs == mock_process_data.outputs

    def test_carbon_capture_rate_delegated(self, mock_process_data):
        """Should delegate carbon_capture_rate to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.carbon_capture_rate == 0.5

    def test_is_capture_process_true(self, mock_process_data):
        """Should return True if carbon_capture_rate > 0."""
        process = AbstractProcess(1, mock_process_data)
        assert process.is_capture_process is True

    def test_is_capture_process_false(self, mock_process_data):
        """Should return False if carbon_capture_rate == 0."""
        mock_process_data.carbon_capture_rate = 0
        process = AbstractProcess(1, mock_process_data)
        assert process.is_capture_process is False

    def test_sector_ids_delegated(self, mock_process_data):
        """Should delegate sector_ids to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.sector_ids == (1, 2)

    def test_lifetime_in_years_delegated(self, mock_process_data):
        """Should delegate lifetime_in_years to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.lifetime_in_years == 25

    def test_tech_available_at_year_delegated(self, mock_process_data):
        """Should delegate tech_available_at_year to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.tech_available_at_year == 2020

    def test_depreciation_period_delegated(self, mock_process_data):
        """Should delegate depreciation_period to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.depreciation_period == 20

    def test_life_extension_factor_delegated(self, mock_process_data):
        """Should delegate life_extension_factor to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.life_extension_factor == 1.2

    def test_non_energy_direct_emission_delegated(self, mock_process_data):
        """Should delegate non_energy_direct_process_emission to process_data."""
        process = AbstractProcess(1, mock_process_data)
        assert process.non_energy_direct_process_emission_in_t_co2_per_process_count == 5.0

    def test_emission_not_implemented(self, mock_process_data):
        """Should raise NotImplementedError for emission property."""
        process = AbstractProcess(1, mock_process_data)
        with pytest.raises(NotImplementedError):
            _ = process.emission

    def test_invest_cost_not_implemented(self, mock_process_data):
        """Should raise NotImplementedError for invest_cost_in_euro_per_process_count."""
        process = AbstractProcess(1, mock_process_data)
        with pytest.raises(NotImplementedError):
            process.invest_cost_in_euro_per_process_count(2025, 0.05, {})

    def test_opex_not_implemented(self, mock_process_data):
        """Should raise NotImplementedError for opex_in_euro_per_process_count."""
        process = AbstractProcess(1, mock_process_data)
        with pytest.raises(NotImplementedError):
            process.opex_in_euro_per_process_count(2025, {})

    def test_compound_factor(self, mock_process_data):
        """Should calculate compound factor correctly."""
        process = AbstractProcess(1, mock_process_data)
        # With interest_rate=0.05 and depreciation_period=20
        # (1.05)^20 ≈ 2.653
        factor = process._compound_factor(0.05)
        assert factor == pytest.approx(2.653, rel=0.01)

    def test_compound_factor_zero_depreciation(self, mock_process_data):
        """Should raise ValueError if depreciation_period is 0."""
        mock_process_data.depreciation_period = 0

        with pytest.raises(ValueError, match='[Dd]epreciation period'):
            AbstractProcess(1, mock_process_data)

    def test_annuity_factor(self, mock_process_data):
        """Should calculate annuity factor correctly."""
        process = AbstractProcess(1, mock_process_data)
        # With interest_rate=0.05 and depreciation_period=20
        factor = process._annuity_factor(0.05)
        assert isinstance(factor, float)
        assert factor > 0

    def test_production_in_unit_per_process_count_unknown_unit(self, mock_process_data):
        """Should raise TypeError for unknown carrier unit."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit='UNKNOWN_UNIT')

        with pytest.raises(TypeError, match='Unknown carrier unit'):
            process._production_in_unit_per_process_count(mock_carrier)

    def test_consumption_in_unit_per_process_count_unknown_unit(self, mock_process_data):
        """Should raise TypeError for unknown carrier unit."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit='UNKNOWN_UNIT')

        with pytest.raises(TypeError, match='Unknown carrier unit'):
            process._consumption_in_unit_per_process_count(2025, mock_carrier)

    def test_production_in_gj(self, mock_process_data):
        """Should calculate total production in GJ."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit=CarrierUnit.GJ)

        # Production should be gj_per_process * execution_count
        production = process.production_in_gj(mock_carrier, 10)
        assert isinstance(production, (int, float))

    def test_netto_produced_or_consumed(self, mock_process_data):
        """Should calculate net produced/consumed amount."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit=CarrierUnit.T)

        netto = process.netto_produced_or_consumed_amount_per_process_count(2025, mock_carrier)
        assert isinstance(netto, (int, float))

    def test_production_in_t_per_process_count(self, mock_process_data):
        """Should delegate production in tons to production calculator."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit=CarrierUnit.T)
        process._prod_cons_calc._production_in_t_per_process_count = Mock(return_value=10.5)

        result = process._production_in_t_per_process_count(mock_carrier)

        assert result == 10.5
        process._prod_cons_calc._production_in_t_per_process_count.assert_called_once_with(mock_carrier)

    def test_production_in_gj_per_process_count(self, mock_process_data):
        """Should delegate production in GJ to production calculator."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit=CarrierUnit.GJ)
        process._prod_cons_calc._production_in_gj_per_process_count = Mock(return_value=25.3)

        result = process._production_in_gj_per_process_count(mock_carrier)

        assert result == 25.3
        process._prod_cons_calc._production_in_gj_per_process_count.assert_called_once_with(mock_carrier)

    def test_consumption_in_t_per_process_count(self, mock_process_data):
        """Should delegate consumption in tons to production calculator."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit=CarrierUnit.T)
        process._prod_cons_calc._consumption_in_t_per_process_count = Mock(return_value=5.2)

        result = process._consumption_in_t_per_process_count(2025, mock_carrier)

        assert result == 5.2
        process._prod_cons_calc._consumption_in_t_per_process_count.assert_called_once_with(2025, mock_carrier)

    def test_consumption_in_gj_per_process_count(self, mock_process_data):
        """Should delegate consumption in GJ to production calculator."""
        process = AbstractProcess(1, mock_process_data)
        mock_carrier = Mock(unit=CarrierUnit.GJ)
        process._prod_cons_calc._consumption_in_gj_per_process_count = Mock(return_value=15.7)

        result = process._consumption_in_gj_per_process_count(2025, mock_carrier)

        assert result == 15.7
        process._prod_cons_calc._consumption_in_gj_per_process_count.assert_called_once_with(2025, mock_carrier)
