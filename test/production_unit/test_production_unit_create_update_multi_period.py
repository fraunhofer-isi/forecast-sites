# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for ProductionUnit._create_or_update_sub_production_units_from_multi_period method."""

import unittest
from unittest import mock

from processes.installed_process import InstalledProcess
from production_unit.production_unit import ProductionUnit


class TestProductionUnitCreateOrUpdateSubProductionUnitsFromMultiPeriod(unittest.TestCase):
    """Test ProductionUnit._create_or_update_sub_production_units_from_multi_period method."""

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

    def test_create_or_update_with_installed_process(self):
        """Test _create_or_update_sub_production_units_from_multi_period with installed process."""
        # Setup: Create mock sub-production unit and installed process
        mock_sub_pu = mock.MagicMock()
        mock_installed_process = mock.MagicMock(spec=InstalledProcess)
        mock_process_option = mock.MagicMock()
        mock_process_option.process = mock_installed_process

        # Setup: Mock optimization results
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.process_execution_counts = {mock_process_option: 5}
        self.pu.optimization_results = mock_optimization_results

        # Setup: Mock sub-production units
        self.pu.sub_production_units = [mock_sub_pu]
        self.pu._find_sub_production_unit_for_installed_process = mock.MagicMock(return_value=mock_sub_pu)
        self.pu._is_future_planned_sub_production_unit = mock.MagicMock(return_value=False)

        # Setup: Mock multi-period result
        mock_new_capacity = {mock_process_option: 10}
        mock_multi_period_result = mock.MagicMock()
        mock_multi_period_result.get_new_capacity_for_year = mock.MagicMock(return_value=mock_new_capacity)
        self.pu._multi_period_result = mock_multi_period_result

        # Execute
        self.pu._create_or_update_sub_production_units_from_multi_period(2021)

        # Verify: Sub-production unit was updated
        assert mock_sub_pu.process_execution_count == 5
        # Verify: Inactivity was reset (execution count > 0)
        assert self.pu._sub_production_unit_inactivity[mock_sub_pu] == 0

    def test_create_or_update_with_zero_execution_count(self):
        """Test _create_or_update_sub_production_units_from_multi_period with zero execution count."""
        # Setup: Create mock sub-production unit and installed process
        mock_sub_pu = mock.MagicMock()
        mock_installed_process = mock.MagicMock(spec=InstalledProcess)
        mock_process_option = mock.MagicMock()
        mock_process_option.process = mock_installed_process

        # Setup: Mock optimization results with zero execution count
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.process_execution_counts = {mock_process_option: 0}
        self.pu.optimization_results = mock_optimization_results

        # Setup: Mock sub-production units
        self.pu.sub_production_units = [mock_sub_pu]
        self.pu._find_sub_production_unit_for_installed_process = mock.MagicMock(return_value=mock_sub_pu)
        self.pu._is_future_planned_sub_production_unit = mock.MagicMock(return_value=False)
        self.pu._sub_production_unit_inactivity[mock_sub_pu] = 0

        # Setup: Mock multi-period result
        mock_new_capacity = {mock_process_option: 0}
        mock_multi_period_result = mock.MagicMock()
        mock_multi_period_result.get_new_capacity_for_year = mock.MagicMock(return_value=mock_new_capacity)
        self.pu._multi_period_result = mock_multi_period_result

        # Execute
        self.pu._create_or_update_sub_production_units_from_multi_period(2021)

        # Verify: Sub-production unit was updated
        assert mock_sub_pu.process_execution_count == 0
        # Verify: Inactivity was incremented (execution count = 0 and not future planned)
        assert self.pu._sub_production_unit_inactivity[mock_sub_pu] == 1

    def test_create_or_update_skips_when_sub_pu_not_found(self):
        """Test _create_or_update_sub_production_units_from_multi_period skips when sub-pu not found."""
        # Setup: Create mock installed process
        mock_installed_process = mock.MagicMock(spec=InstalledProcess)
        mock_process_option = mock.MagicMock()
        mock_process_option.process = mock_installed_process

        # Setup: Mock optimization results
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.process_execution_counts = {mock_process_option: 5}
        self.pu.optimization_results = mock_optimization_results

        # Setup: Mock sub-production units (empty)
        self.pu.sub_production_units = []
        self.pu._find_sub_production_unit_for_installed_process = mock.MagicMock(return_value=None)

        # Setup: Mock multi-period result
        mock_new_capacity = {mock_process_option: 10}
        mock_multi_period_result = mock.MagicMock()
        mock_multi_period_result.get_new_capacity_for_year = mock.MagicMock(return_value=mock_new_capacity)
        self.pu._multi_period_result = mock_multi_period_result

        # Execute (should not raise)
        self.pu._create_or_update_sub_production_units_from_multi_period(2021)

        # Verify: No errors occurred
        self.pu._find_sub_production_unit_for_installed_process.assert_called_once_with(mock_installed_process)

    def test_split_execution_across_vintages_with_zero_execution(self):
        """Test _split_execution_across_vintages increments inactivity for zero execution."""
        # Setup: Create mock vintage sub-production units
        mock_vintage_1 = mock.MagicMock()
        mock_vintage_1.max_process_execution_count = 10
        mock_vintage_1.process_execution_count = 0

        mock_vintage_2 = mock.MagicMock()
        mock_vintage_2.max_process_execution_count = 10
        mock_vintage_2.process_execution_count = 0

        vintages = [mock_vintage_1, mock_vintage_2]

        # Setup: Mock future-planned check to return False (not future-planned)
        self.pu._is_future_planned_sub_production_unit = mock.MagicMock(return_value=False)

        # Setup: Initialize inactivity tracking
        self.pu._sub_production_unit_inactivity = {}

        # Execute: Split zero execution across vintages
        self.pu._split_execution_across_vintages(vintages, total_execution_count=0, year=2021)

        # Verify: Both vintages have zero execution count
        assert mock_vintage_1.process_execution_count == 0
        assert mock_vintage_2.process_execution_count == 0

        # Verify: Inactivity was incremented for both (line 605-606 executed)
        assert self.pu._sub_production_unit_inactivity[mock_vintage_1] == 1
        assert self.pu._sub_production_unit_inactivity[mock_vintage_2] == 1

    def test_create_or_update_skips_inactivity_for_future_planned(self):
        """Test that future-planned sub-PUs don't get inactivity incremented (branch 538->528)."""
        mock_sub_pu = mock.MagicMock()
        mock_installed_process = mock.MagicMock(spec=InstalledProcess)
        mock_process_option = mock.MagicMock()
        mock_process_option.process = mock_installed_process

        # Zero execution count
        mock_optimization_results = mock.MagicMock()
        mock_optimization_results.process_execution_counts = {mock_process_option: 0}
        self.pu.optimization_results = mock_optimization_results

        self.pu.sub_production_units = [mock_sub_pu]
        self.pu._find_sub_production_unit_for_installed_process = mock.MagicMock(return_value=mock_sub_pu)
        # IS future planned → elif is False → branch 538->528
        self.pu._is_future_planned_sub_production_unit = mock.MagicMock(return_value=True)

        mock_new_capacity = {mock_process_option: 0}
        mock_multi_period_result = mock.MagicMock()
        mock_multi_period_result.get_new_capacity_for_year = mock.MagicMock(return_value=mock_new_capacity)
        self.pu._multi_period_result = mock_multi_period_result

        self.pu._create_or_update_sub_production_units_from_multi_period(2021)

        # Verify: Inactivity was NOT incremented (future planned)
        assert mock_sub_pu not in self.pu._sub_production_unit_inactivity
