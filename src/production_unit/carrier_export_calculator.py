# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class CarrierExportCalculator:
    """Calculates carrier export amounts with numerical tolerance handling."""

    EPSILON = 1e-3  # Numerical tolerance for export calculations

    @staticmethod
    def normalize_export_amount(export_amount, carrier=None):
        """Normalize export amount, handling small negative values due to numerical precision.

        Args:
            export_amount: The calculated export amount
            carrier: The carrier (for error messages)

        Returns:
            The normalized export amount (0 if small negative, original if positive)

        Raises:
            ValueError: If export is significantly negative (< -epsilon)
        """
        if export_amount < 0:
            if export_amount < -CarrierExportCalculator.EPSILON:
                message = f'Export for carrier {carrier} must not be negative: {export_amount}.'
                raise ValueError(message)
            # Round to zero for further processing
            return 0.0
        return export_amount
