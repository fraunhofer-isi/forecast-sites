# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class _RegionNewCapacityAdapter:
    """
    Adapts per-PU new_capacity dict to the interface expected by PU._create_or_update_sub_production_units_from_multi_period.

    That method reads self._multi_period_result.get_new_capacity_for_year(year),
    so this adapter provides that method, ignoring year (the caller already sliced by year).
    """

    def __init__(self, new_capacity_counts):
        self._new_capacity_counts = new_capacity_counts

    def get_new_capacity_for_year(self, year):
        return self._new_capacity_counts
