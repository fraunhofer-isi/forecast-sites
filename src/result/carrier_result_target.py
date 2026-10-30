# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from dataclasses import dataclass


@dataclass(frozen=True)
class CarrierResultTarget:
    """Represents the result of dispatching a carrier to its appropriate handler."""

    kind: str  # 'energy_carrier', 'product', or 'by_product'
    id_value: int  # The ID to use in the result table
    unit_suffix: str  # '' or '_in_gj' or '_in_t'
