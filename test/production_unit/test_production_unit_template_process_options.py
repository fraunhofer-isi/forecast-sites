# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit template process options handling."""

import unittest
from unittest import mock

from production_unit.production_unit import ProductionUnit


class TestProductionUnitTemplateProcessOptions(unittest.TestCase):
    """Test ProductionUnit template process options handling."""

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

    def test_create_or_update_with_template_process_new_capacity(self):
        """Test _create_or_update_sub_production_units_from_multi_period with template process and new capacity."""
        # Setup: Create mock template process (not installed)
        mock_template_process = mock.MagicMock()
        mock_template_process.id = 'template_1'
        mock_process_option = mock.MagicMock()
        mock_process_option.process = mock_template_process

        # Setup: Mock optimization results with template process
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.process_execution_counts = {mock_process_option: 10}
        self.pu.optimization_results = mock_optimization_results

        # Setup: Mock sub-production units (empty initially)
        self.pu.sub_production_units = []
        self.pu._find_sub_production_unit_for_installed_process = mock.MagicMock(return_value=None)

        # Setup: Mock multi-period result with new capacity
        mock_new_capacity = {mock_process_option: 5}
        mock_multi_period_result = mock.MagicMock()
        mock_multi_period_result.get_new_capacity_for_year = mock.MagicMock(return_value=mock_new_capacity)
        self.pu._multi_period_result = mock_multi_period_result

        # Setup: Mock factory to create new sub-production unit
        mock_new_sub_pu = mock.MagicMock()
        mock_new_sub_pu.installed_process.id = 'template_1'
        mock_new_sub_pu.max_process_execution_count = 5
        self.pu._sub_production_unit_factory.create_sub_production_unit_for_process_option = mock.MagicMock(
            return_value=mock_new_sub_pu
        )

        # Setup: Mock split execution method
        self.pu._split_execution_across_vintages = mock.MagicMock()

        # Execute
        self.pu._create_or_update_sub_production_units_from_multi_period(2021)

        # Verify: New sub-production unit was created
        self.pu._sub_production_unit_factory.create_sub_production_unit_for_process_option.assert_called_once_with(
            mock_process_option,
            5,
            self.pu,
            2021,
        )
        # Verify: New sub-production unit was added
        assert mock_new_sub_pu in self.pu.sub_production_units
        # Verify: Inactivity was initialized
        assert self.pu._sub_production_unit_inactivity[mock_new_sub_pu] == 0

    def test_create_or_update_skips_template_with_zero_capacity(self):
        """Test _create_or_update_sub_production_units_from_multi_period skips template with zero capacity."""
        # Setup: Create mock template process
        mock_template_process = mock.MagicMock()
        mock_process_option = mock.MagicMock()
        mock_process_option.process = mock_template_process

        # Setup: Mock optimization results
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.process_execution_counts = {mock_process_option: 10}
        self.pu.optimization_results = mock_optimization_results

        # Setup: Mock sub-production units
        self.pu.sub_production_units = []

        # Setup: Mock multi-period result with zero new capacity
        mock_new_capacity = {mock_process_option: 0}
        mock_multi_period_result = mock.MagicMock()
        mock_multi_period_result.get_new_capacity_for_year = mock.MagicMock(return_value=mock_new_capacity)
        self.pu._multi_period_result = mock_multi_period_result

        # Setup: Mock factory
        self.pu._sub_production_unit_factory.create_sub_production_unit_for_process_option = mock.MagicMock()

        # Execute
        self.pu._create_or_update_sub_production_units_from_multi_period(2021)

        # Verify: Factory was not called (zero capacity skipped)
        self.pu._sub_production_unit_factory.create_sub_production_unit_for_process_option.assert_not_called()
