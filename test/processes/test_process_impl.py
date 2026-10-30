# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock, patch

from processes.process import Process


def _create_process_data():
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


def test_efficiency_improvement_delegates_to_interpolator():
    process = Process(1, _create_process_data())

    with patch('processes.process.interpolator.interpolate', return_value=0.25) as interpolate:
        result = process._efficiency_improvement(2030, {'mode': 'test'})

    assert result == 0.25
    interpolate.assert_called_once_with(2030, {'mode': 'test'}, process.efficiency_improvement_interpolation_data)
