# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class CarrierNettoAmountCalculator:
    """
    Calculate carrier netto amounts from LP process execution counts.

    LP result is the source of truth for PU-level carrier balances.
    This calculator derives the netto produced/consumed amount per carrier
    directly from the optimized execution counts and process coefficients,
    so that reported exports are consistent with what the LP constrained.
    """

    def calculate(self, process_execution_counts, carriers, year):
        """
        Return netto carrier amounts keyed by carrier.

        Args:
            process_execution_counts: dict mapping ProcessOption -> float exec count
            carriers: iterable of carrier objects
            year: simulation year (int)

        Returns:
            dict mapping carrier -> float netto amount (positive = produced, negative = consumed)

        """
        netto_amounts = {}
        for carrier in carriers:
            total = 0.0
            for process_option, exec_count in process_execution_counts.items():
                coefficient = process_option.process.netto_produced_or_consumed_amount_per_process_count(year, carrier)
                total += exec_count * coefficient
            netto_amounts[carrier] = total
        return netto_amounts
