# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for CollectingResultVisitor carrier type handling."""

import unittest
from unittest import mock

import pytest

from by_product.by_product import ByProduct
from carrier.carrier_unit import CarrierUnit
from product.product import Product
from result.collecting_result_visitor import CollectingResultVisitor


class TestCollectingResultVisitorCarrierTypeHandling(unittest.TestCase):
    """Test CollectingResultVisitor handling of different carrier types."""

    def setUp(self):
        """Set up test fixtures."""
        self.visitor = CollectingResultVisitor({'start_year': 2020})
        self.visitor._initialize()

    def test_handle_production_unit_carrier_result_with_product(self):
        """Test handling production unit carrier result with Product carrier."""
        mock_product = mock.MagicMock(spec=Product)
        mock_product.unit = CarrierUnit.T
        mock_product.id = 'product_1'

        carrier_result = {mock_product: 100.0}

        with mock.patch.object(self.visitor, '_add_production_unit_product_entry') as mock_add:
            self.visitor._handle_production_unit_carrier_result(carrier_result, 'purchased_amount', 2020, append_unit=True)
            mock_add.assert_called_once()

    def test_handle_production_unit_carrier_result_with_by_product(self):
        """Test handling production unit carrier result with ByProduct carrier."""
        mock_by_product = mock.MagicMock(spec=ByProduct)
        mock_by_product.unit = CarrierUnit.T
        mock_by_product.id = 'by_product_1'

        carrier_result = {mock_by_product: 50.0}

        with mock.patch.object(self.visitor, '_add_production_unit_by_product_entry') as mock_add:
            self.visitor._handle_production_unit_carrier_result(carrier_result, 'purchased_amount', 2020, append_unit=True)
            mock_add.assert_called_once()

    def test_handle_production_unit_carrier_result_unknown_t_carrier_raises(self):
        """Test that unknown T carrier type raises NotImplementedError."""
        mock_unknown_carrier = mock.MagicMock()
        mock_unknown_carrier.unit = CarrierUnit.T
        # Not a Product or ByProduct

        carrier_result = {mock_unknown_carrier: 75.0}

        with pytest.raises(NotImplementedError, match='not yet implemented'):
            self.visitor._handle_production_unit_carrier_result(carrier_result, 'purchased_amount', 2020)

    def test_handle_production_unit_carrier_result_unknown_unit_raises(self):
        """Test that unknown carrier unit raises ValueError."""
        mock_carrier = mock.MagicMock()
        mock_carrier.unit = 'UNKNOWN_UNIT'  # Not GJ or T

        carrier_result = {mock_carrier: 25.0}

        with pytest.raises(ValueError, match='Unknown carrier unit'):
            self.visitor._handle_production_unit_carrier_result(carrier_result, 'purchased_amount', 2020)
