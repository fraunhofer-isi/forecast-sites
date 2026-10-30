# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Process data property accessors.

This module encapsulates direct delegation to ProcessDataSpec,
separating data layer access from business logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from processes.process_data_spec import ProcessDataSpec


class ProcessDataProperties:
    """
    Accessor for process data specification properties.

    Provides unified interface to ProcessDataSpec attributes,
    enabling data layer separation from core process logic.
    """

    def __init__(self, process_data: ProcessDataSpec):
        """
        Initialize with process data specification.

        Args:
            process_data: ProcessDataSpec instance containing process metadata.

        """
        self._process_data = process_data

    @property
    def demands(self) -> tuple[Any]:
        """Get process input demands (carriers consumed)."""
        return self._process_data.demands

    @property
    def outputs(self) -> tuple[Any]:
        """Get process outputs (carriers produced)."""
        return self._process_data.outputs

    @property
    def carbon_capture_rate(self) -> float:
        """Get carbon capture rate (0-1, fraction of direct emissions captured)."""
        return self._process_data.carbon_capture_rate

    @property
    def is_capture_process(self) -> bool:
        """Check if this process captures carbon (carbon_capture_rate > 0)."""
        return self.carbon_capture_rate > 0

    @property
    def sector_ids(self) -> tuple[int]:
        """Get sector IDs this process belongs to."""
        return self._process_data.sector_ids

    @property
    def lifetime_in_years(self) -> int:
        """Get expected process lifetime in years."""
        return self._process_data.lifetime_in_years

    @property
    def tech_available_at_year(self) -> int:
        """Get first year this technology is available."""
        return self._process_data.tech_available_at_year

    @property
    def depreciation_period(self) -> int:
        """Get accounting depreciation period in years."""
        return self._process_data.depreciation_period

    @property
    def life_extension_factor(self) -> float:
        """Get cost extension factor for operating beyond lifetime."""
        return self._process_data.life_extension_factor

    @property
    def non_energy_direct_process_emission_in_t_co2_per_process_count(self) -> float:
        """Get direct (scope 1) emissions per process execution."""
        return self._process_data.non_energy_direct_process_emission_in_t_co2_per_process_count

    @property
    def capex_interpolation_data_in_euro_per_process_count(self):
        """Get capital expenditure cost interpolation data."""
        return self._process_data.capex_interpolation_data_in_euro_per_process_count

    @property
    def opex_interpolation_data_in_euro_per_process_count(self):
        """Get operating expenditure cost interpolation data."""
        return self._process_data.opex_interpolation_data_in_euro_per_process_count

    @property
    def investment_funding_interpolation_data_in_euro_per_process_count(self):
        """Get investment funding cost interpolation data."""
        return self._process_data.investment_funding_interpolation_data_in_euro_per_process_count

    @property
    def efficiency_improvement_interpolation_data(self):
        """Get efficiency improvement factor interpolation data."""
        return self._process_data.efficiency_improvement_interpolation_data
