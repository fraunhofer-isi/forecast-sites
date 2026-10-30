# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest

from interpolation.interpolation_data import InterpolationData
from processes.process_data import ProcessData


class TestProcessData:
    """Test the ProcessData class."""

    @pytest.fixture
    def process_entry(self):
        """Create a mock process entry."""
        return {
            'carbon_capture_rate': 0.5,
            'lifetime_in_years': 25,
            'tech_available_at_year': 2020,
            'depreciation_period': 20,
            'life_extension_factor': 1.2,
            'non_energy_direct_process_emission_in_t_co2_per_process_count': 5.0,
            'capex_start_year_in_euro_per_process_count': 100000,
            'capex_end_year_in_euro_per_process_count': 80000,
            'opex_start_year_in_euro_per_process_count': 10000,
            'opex_end_year_in_euro_per_process_count': 8000,
            'investment_funding_start_year_in_euro_per_process_count': 50000,
            'investment_funding_end_year_in_euro_per_process_count': 40000,
            'efficiency_improvement_start_year': 0.0,
            'efficiency_improvement_end_year': 0.1,
        }

    @pytest.fixture
    def sample_demands(self):
        """Create sample demands."""
        return (Mock(name='Demand1'), Mock(name='Demand2'))

    @pytest.fixture
    def sample_outputs(self):
        """Create sample outputs."""
        return (Mock(name='Output1'), Mock(name='Output2'))

    @pytest.fixture
    def sample_sector_ids(self):
        """Create sample sector IDs."""
        return (1, 2, 3)

    def test_initialization(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should initialize with all required data."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data is not None

    def test_demands_stored(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should store demands."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.demands == sample_demands

    def test_outputs_stored(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should store outputs."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.outputs == sample_outputs

    def test_sector_ids_stored(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should store sector IDs."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.sector_ids == sample_sector_ids

    def test_carbon_capture_rate(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should extract and store carbon capture rate."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.carbon_capture_rate == 0.5

    def test_lifetime_in_years(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should extract and store lifetime."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.lifetime_in_years == 25

    def test_tech_available_at_year(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should extract and store technology availability year."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.tech_available_at_year == 2020

    def test_depreciation_period(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should extract and store depreciation period."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.depreciation_period == 20

    def test_life_extension_factor(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should extract and store life extension factor."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.life_extension_factor == 1.2

    def test_non_energy_direct_emission(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should extract and store non-energy direct emissions."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert data.non_energy_direct_process_emission_in_t_co2_per_process_count == 5.0

    def test_capex_interpolation_data(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should create capex interpolation data."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert isinstance(data.capex_interpolation_data_in_euro_per_process_count, InterpolationData)
        assert data.capex_interpolation_data_in_euro_per_process_count.value_for_start_year == 100000
        assert data.capex_interpolation_data_in_euro_per_process_count.value_for_end_year == 80000

    def test_opex_interpolation_data(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should create opex interpolation data."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert isinstance(data.opex_interpolation_data_in_euro_per_process_count, InterpolationData)
        assert data.opex_interpolation_data_in_euro_per_process_count.value_for_start_year == 10000
        assert data.opex_interpolation_data_in_euro_per_process_count.value_for_end_year == 8000

    def test_investment_funding_interpolation_data(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """
        Should create investment funding interpolation data without an interim year.

        The absent interim year is a deliberate modeling decision, confirmed by the
        domain owner in `bd show forecast-sites-private-6zj.19`: the funding follows a
        straight line over the whole simulation. Real funding programs are stepped and
        time-limited, so the temptation to add an interim year is real -- do not.
        Energy carrier subsidies are the only interpolation in `src/` that has one.
        """
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert isinstance(data.investment_funding_interpolation_data_in_euro_per_process_count, InterpolationData)
        assert data.investment_funding_interpolation_data_in_euro_per_process_count.value_for_start_year == 50000
        assert data.investment_funding_interpolation_data_in_euro_per_process_count.value_for_end_year == 40000
        assert data.investment_funding_interpolation_data_in_euro_per_process_count.value_for_interim_year is None

    def test_efficiency_improvement_interpolation_data(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should create efficiency improvement interpolation data."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)
        assert isinstance(data.efficiency_improvement_interpolation_data, InterpolationData)
        assert data.efficiency_improvement_interpolation_data.value_for_start_year == 0.0
        assert data.efficiency_improvement_interpolation_data.value_for_end_year == 0.1

    def test_immutability(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """ProcessData should be immutable after initialization."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)

        with pytest.raises(AttributeError):
            data.carbon_capture_rate = 0.8

    def test_cannot_add_attributes(self, process_entry, sample_demands, sample_outputs, sample_sector_ids):
        """Should not allow adding new attributes after initialization."""
        data = ProcessData(process_entry, sample_demands, sample_outputs, sample_sector_ids)

        with pytest.raises(AttributeError):
            data.new_field = 'value'
