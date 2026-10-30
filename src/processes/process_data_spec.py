# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from demand.demand import Demand
    from interpolation.interpolation_data import InterpolationData
    from output.output import Output


@runtime_checkable
class ProcessDataSpec(Protocol):
    """
    Structural interface required by AbstractProcess and Process.

    Any object providing these attributes (typically ProcessData) can serve
    as the specification / immutable data backbone of a processes instance.
    """

    demands: tuple[Demand]
    outputs: tuple[Output]

    # only used by carbon capture processes
    carbon_capture_rate: float

    # restricts the process to certain sectors, empty means all sectors
    sector_ids: tuple[int]

    lifetime_in_years: int

    tech_available_at_year: int

    depreciation_period: int

    life_extension_factor: float

    non_energy_direct_process_emission_in_t_co2_per_process_count: float

    capex_interpolation_data_in_euro_per_process_count: InterpolationData
    opex_interpolation_data_in_euro_per_process_count: InterpolationData
    investment_funding_interpolation_data_in_euro_per_process_count: InterpolationData
    efficiency_improvement_interpolation_data: InterpolationData
