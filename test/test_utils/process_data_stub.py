# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessDataStub:
    demands: tuple[Any, ...] = field(default_factory=tuple)
    outputs: tuple[Any, ...] = field(default_factory=tuple)
    carbon_capture_rate: float = 0.0
    sector_ids: tuple[int, ...] = field(default_factory=tuple)
    lifetime_in_years: int = 10
    tech_available_at_year: int = 2020
    depreciation_period: int = 5
    life_extension_factor: float = 0.1
    non_energy_direct_process_emission_in_t_co2_per_process_count: float = 0.0
    capex_interpolation_data_in_euro_per_process_count: Any = None
    opex_interpolation_data_in_euro_per_process_count: Any = None
    investment_funding_interpolation_data_in_euro_per_process_count: Any = None
    efficiency_improvement_interpolation_data: Any = None


def make_process_data_stub(**overrides: Any) -> ProcessDataStub:
    process_data = ProcessDataStub()
    for key, value in overrides.items():
        setattr(process_data, key, value)
    return process_data
