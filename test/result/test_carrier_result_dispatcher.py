# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from unittest.mock import MagicMock

from carrier.carrier_unit import CarrierUnit
from result.carrier_result_dispatcher import CarrierResultDispatcher


class TestCarrierResultDispatcher:
    """Tests for CarrierResultDispatcher.dispatch()."""

    def test_dispatch_energy_carrier(self):
        """Test dispatching an energy carrier (GJ unit)."""
        carrier = MagicMock()
        carrier.unit = CarrierUnit.GJ
        carrier.id = 42

        target = CarrierResultDispatcher.dispatch(carrier)

        assert target.kind == 'energy_carrier'
        assert target.id_value == 42
        assert target.unit_suffix == '_in_gj'

    def test_dispatch_product(self):
        """Test dispatching a product (T unit)."""
        from product.product import Product

        carrier = MagicMock(spec=Product)
        carrier.unit = CarrierUnit.T
        carrier.id = 123

        target = CarrierResultDispatcher.dispatch(carrier)

        assert target.kind == 'product'
        assert target.id_value == 123
        assert target.unit_suffix == '_in_t'

    def test_dispatch_by_product(self):
        """Test dispatching a by-product (T unit)."""
        from by_product.by_product import ByProduct

        carrier = MagicMock(spec=ByProduct)
        carrier.unit = CarrierUnit.T
        carrier.id = 456

        target = CarrierResultDispatcher.dispatch(carrier)

        assert target.kind == 'by_product'
        assert target.id_value == 456
        assert target.unit_suffix == '_in_t'

    def test_dispatch_unknown_carrier_type_raises_not_implemented(self):
        """Test that unknown carrier type raises NotImplementedError."""
        carrier = MagicMock()
        carrier.unit = CarrierUnit.T
        carrier.__class__.__name__ = 'UnknownCarrier'

        with pytest.raises(NotImplementedError, match='not yet implemented'):
            CarrierResultDispatcher.dispatch(carrier)

    def test_dispatch_unknown_unit_raises_value_error(self):
        """Test that unknown carrier unit raises ValueError."""
        carrier = MagicMock()
        carrier.unit = 'UNKNOWN'

        with pytest.raises(ValueError, match='Unknown carrier unit'):
            CarrierResultDispatcher.dispatch(carrier)
