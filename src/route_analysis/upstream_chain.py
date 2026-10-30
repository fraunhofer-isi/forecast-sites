# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from dataclasses import dataclass, field


@dataclass
class UpstreamChain:
    """Represents an upstream supply chain for a product."""

    process_ids: set[int] = field(default_factory=set)
    energy_demands: list[tuple[int, int, float, str]] = field(default_factory=list)
    internal_carrier_pool_inputs: list[tuple[int, int, float]] = field(default_factory=list)
    purchased_carrier_flows: list[tuple[int, int, float]] = field(default_factory=list)
    product_flows: list[tuple[int, int, int, float]] = field(default_factory=list)
    purchased_product_flows: list[tuple[int, int, float]] = field(default_factory=list)
    by_product_flows: list[tuple[int, int, int, float]] = field(default_factory=list)
    purchased_by_product_flows: list[tuple[int, int, float]] = field(default_factory=list)
    carrier_flows: list[tuple[int, int, int, float]] = field(default_factory=list)
    final_product_outputs: list[tuple[int, int, float]] = field(default_factory=list)
