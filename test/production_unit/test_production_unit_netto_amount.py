# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit._export_amount_for_carrier method."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitExportAmountForCarrier(unittest.TestCase):
    """Test ProductionUnit._export_amount_for_carrier method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_site = mock.MagicMock()
        self.mock_sub_pu_factory = mock.MagicMock()
        self.mock_sub_pu_factory.create_for_start_year.return_value = []
        self.mock_optimization_factory = mock.MagicMock()
        self.mock_process_map = {}
        self.mock_carriers = {}
        self.mock_simulation_options = {
            'rolling_planning_horizon_in_years': 5,
            'start_year': 2020,
        }
        self.mock_minimum_export_data = {}

        self.pu = ProductionUnit(
            id_production_unit=1,
            site=self.mock_site,
            sector='steel',
            minimum_export_interpolation_data_in_t=self.mock_minimum_export_data,
            sub_production_unit_factory=self.mock_sub_pu_factory,
            optimization_factory=self.mock_optimization_factory,
            process_map=self.mock_process_map,
            carriers=self.mock_carriers,
            simulation_options=self.mock_simulation_options,
        )

    def test_export_with_optimized_netto_amounts(self):
        """Test _export_amount_for_carrier with optimized netto amounts."""
        # Setup: Create mock carrier and optimization results
        mock_carrier = mock.MagicMock()
        mock_netto_amounts = {mock_carrier: 42.5}
        mock_purchased_amounts = {mock_carrier: 10.0}
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.carrier_netto_amounts = mock_netto_amounts
        mock_optimization_results.purchased_carrier_amounts = mock_purchased_amounts
        self.pu.optimization_results = mock_optimization_results

        # Execute
        result = self.pu._export_amount_for_carrier(2021, mock_carrier)

        # Verify: Export = purchased + netto = 10.0 + 42.5 = 52.5
        assert result == 52.5

    def test_export_with_no_optimized_netto_amounts(self):
        """Test _export_amount_for_carrier with no optimized netto amounts."""
        # Setup: Create mock carrier and optimization results
        mock_carrier = mock.MagicMock()
        mock_purchased_amounts = {mock_carrier: 10.0}
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.carrier_netto_amounts = None
        mock_optimization_results.purchased_carrier_amounts = mock_purchased_amounts
        self.pu.optimization_results = mock_optimization_results

        # Setup: Mock the sub-production unit method
        self.pu._netto_produced_or_consumed_amount_for_carrier_from_sub_production_units = mock.MagicMock(return_value=15.3)

        # Execute
        result = self.pu._export_amount_for_carrier(2021, mock_carrier)

        # Verify: Export = purchased + netto = 10.0 + 15.3 = 25.3
        assert result == 25.3

    def test_export_with_empty_optimized_netto_amounts(self):
        """Test _export_amount_for_carrier with empty optimized netto amounts."""
        # Setup: Create mock carrier and optimization results
        mock_carrier = mock.MagicMock()
        mock_purchased_amounts = {mock_carrier: 10.0}
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.carrier_netto_amounts = {}
        mock_optimization_results.purchased_carrier_amounts = mock_purchased_amounts
        self.pu.optimization_results = mock_optimization_results

        # Setup: Mock the sub-production unit method
        self.pu._netto_produced_or_consumed_amount_for_carrier_from_sub_production_units = mock.MagicMock(return_value=8.7)

        # Execute
        result = self.pu._export_amount_for_carrier(2021, mock_carrier)

        # Verify: Empty dict is falsy, so falls back to sub-production units
        assert result == 18.7  # 10.0 + 8.7
