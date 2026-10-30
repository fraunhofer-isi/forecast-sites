# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from immutable.immutable import Immutable
from interpolation.interpolation_data import InterpolationData
from processes.process_data_spec import ProcessDataSpec

if TYPE_CHECKING:
    from collections.abc import Mapping

    from demand.demand import Demand
    from output.output import Output


class ProcessData(Immutable, ProcessDataSpec):
    def __init__(
        self,
        process_entry: Mapping[str, Any],
        demands: tuple[Demand],
        outputs: tuple[Output],
        sector_ids: tuple[int],
    ) -> None:
        self.demands = demands
        self.outputs = outputs
        self.carbon_capture_rate = float(process_entry['carbon_capture_rate'])
        self.sector_ids = sector_ids
        self.lifetime_in_years = int(process_entry['lifetime_in_years'])
        self.tech_available_at_year = int(process_entry['tech_available_at_year'])

        self.depreciation_period = int(process_entry['depreciation_period'])
        self.life_extension_factor = float(process_entry['life_extension_factor'])

        self.non_energy_direct_process_emission_in_t_co2_per_process_count = float(
            process_entry['non_energy_direct_process_emission_in_t_co2_per_process_count']
        )

        self.capex_interpolation_data_in_euro_per_process_count = InterpolationData(
            process_entry['capex_start_year_in_euro_per_process_count'],
            process_entry['capex_end_year_in_euro_per_process_count'],
        )

        self.opex_interpolation_data_in_euro_per_process_count = InterpolationData(
            process_entry['opex_start_year_in_euro_per_process_count'],
            process_entry['opex_end_year_in_euro_per_process_count'],
        )

        self.investment_funding_interpolation_data_in_euro_per_process_count = InterpolationData(
            process_entry['investment_funding_start_year_in_euro_per_process_count'],
            process_entry['investment_funding_end_year_in_euro_per_process_count'],
        )

        self.efficiency_improvement_interpolation_data = InterpolationData(
            process_entry['efficiency_improvement_start_year'],
            process_entry['efficiency_improvement_end_year'],
        )
        super().__init__()
