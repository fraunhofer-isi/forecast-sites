# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from by_product.by_product import ByProduct
from carrier.carrier_unit import CarrierUnit
from energy_carrier.energy_carrier import EnergyCarrier
from product.product import Product
from result.carrier_result_target import CarrierResultTarget


class CarrierResultDispatcher:
    """Dispatches carriers to their appropriate result handlers based on type and unit."""

    @staticmethod
    def dispatch(carrier) -> CarrierResultTarget:
        """Dispatch a carrier to its result target.

        Args:
            carrier: An EnergyCarrier, Product, or ByProduct instance

        Returns:
            CarrierResultTarget with kind, id, and unit suffix

        Raises:
            NotImplementedError: If carrier type is not recognized
            ValueError: If carrier unit is not recognized
        """
        carrier_unit = carrier.unit

        if carrier_unit == CarrierUnit.GJ:
            return CarrierResultTarget(
                kind='energy_carrier',
                id_value=carrier.id,
                unit_suffix='_in_gj',
            )
        elif carrier_unit == CarrierUnit.T:
            if isinstance(carrier, Product):
                return CarrierResultTarget(
                    kind='product',
                    id_value=carrier.id,
                    unit_suffix='_in_t',
                )
            elif isinstance(carrier, ByProduct):
                return CarrierResultTarget(
                    kind='by_product',
                    id_value=carrier.id,
                    unit_suffix='_in_t',
                )
            else:
                message = f'Carrier {type(carrier)} not yet implemented'
                raise NotImplementedError(message)
        else:
            message = f'Unknown carrier unit {carrier_unit}'
            raise ValueError(message)
