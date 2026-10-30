# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for Pipelines class."""

import unittest
from unittest import mock

from pipelines.pipelines import Pipelines


class TestPipelinesUpdateModes(unittest.TestCase):
    """Tests for Pipelines.update_modes method."""

    @mock.patch('pipelines.pipelines.geopandas.read_file')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_update_modes_year_before_commissioning(self, mock_file, mock_read_file):
        """Test update_modes when year is before commissioning year."""
        # Setup mock data
        mock_df = mock.MagicMock()
        mock_df.index = [0, 1]
        mock_df.loc = {
            0: mock.MagicMock(**{'__getitem__.side_effect': lambda x: 2030 if x == 'Commissioning Year First' else None}),
            1: mock.MagicMock(**{'__getitem__.side_effect': lambda x: 2035 if x == 'Commissioning Year First' else None}),
        }
        mock_df.__getitem__ = mock.MagicMock(return_value=[mock.MagicMock(), mock.MagicMock()])
        mock_read_file.return_value = mock_df

        mock_file.return_value.__enter__.return_value.read.return_value = '{"features": []}'

        with mock.patch('pipelines.pipelines.json.load') as mock_json:
            mock_json.return_value = {'features': []}
            pipelines = Pipelines()
            pipelines.update_modes(2025)

            # Year 2025 is before both commissioning years (2030, 2035)
            # So no modes should be set to 'H2'
            assert len(pipelines.modes) == 0

    @mock.patch('pipelines.pipelines.geopandas.read_file')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_update_modes_year_after_commissioning(self, mock_file, mock_read_file):
        """Test update_modes when year is after commissioning year."""
        # Setup mock data
        mock_df = mock.MagicMock()
        mock_df.index = [0]
        mock_df.loc = {
            0: mock.MagicMock(**{'__getitem__.side_effect': lambda x: 2020 if x == 'Commissioning Year First' else None}),
        }
        mock_df.__getitem__ = mock.MagicMock(return_value=[mock.MagicMock()])
        mock_read_file.return_value = mock_df

        mock_file.return_value.__enter__.return_value.read.return_value = '{"features": []}'

        with mock.patch('pipelines.pipelines.json.load') as mock_json:
            feature = {
                'properties': {
                    'Commissioning Year First': 2020,
                    'mode': '',
                    'color': '',
                }
            }
            mock_json.return_value = {'features': [feature]}
            pipelines = Pipelines()
            pipelines.update_modes(2025)

            # Year 2025 is after commissioning year 2020
            # So mode should be set to 'H2'
            assert len(pipelines.modes) == 1
            assert pipelines.modes[0] == 'H2'
            assert feature['properties']['color'] == 'limegreen'

    @mock.patch('pipelines.pipelines.geopandas.read_file')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_update_modes_year_equals_commissioning_year(self, mock_file, mock_read_file):
        """Test when year equals commissioning year (boundary condition)."""
        # Setup mock data
        mock_df = mock.MagicMock()
        mock_df.index = [0]
        mock_df.loc = {
            0: mock.MagicMock(**{'__getitem__.side_effect': lambda x: 2025 if x == 'Commissioning Year First' else None}),
        }
        mock_df.__getitem__ = mock.MagicMock(return_value=[mock.MagicMock()])
        mock_read_file.return_value = mock_df

        mock_file.return_value.__enter__.return_value.read.return_value = '{"features": []}'

        with mock.patch('pipelines.pipelines.json.load') as mock_json:
            feature = {
                'properties': {
                    'Commissioning Year First': 2025,
                    'mode': '',
                    'color': '',
                }
            }
            mock_json.return_value = {'features': [feature]}
            pipelines = Pipelines()
            pipelines.update_modes(2025)

            # Year 2025 equals commissioning year 2025
            # So mode should be set to 'H2' (year >= reference_year)
            assert len(pipelines.modes) == 1
            assert pipelines.modes[0] == 'H2'
            assert feature['properties']['color'] == 'limegreen'

    @mock.patch('pipelines.pipelines.geopandas.read_file')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_update_modes_mixed_years(self, mock_file, mock_read_file):
        """Test with mixed years (some before, some after commissioning)."""
        # Setup mock data
        mock_df = mock.MagicMock()
        mock_df.index = [0, 1]
        mock_df.loc = {
            0: mock.MagicMock(**{'__getitem__.side_effect': lambda x: 2020 if x == 'Commissioning Year First' else None}),
            1: mock.MagicMock(**{'__getitem__.side_effect': lambda x: 2030 if x == 'Commissioning Year First' else None}),
        }
        mock_df.__getitem__ = mock.MagicMock(return_value=[mock.MagicMock(), mock.MagicMock()])
        mock_read_file.return_value = mock_df

        mock_file.return_value.__enter__.return_value.read.return_value = '{"features": []}'

        with mock.patch('pipelines.pipelines.json.load') as mock_json:
            feature1 = {
                'properties': {
                    'Commissioning Year First': 2020,
                    'mode': '',
                    'color': '',
                }
            }
            feature2 = {
                'properties': {
                    'Commissioning Year First': 2030,
                    'mode': '',
                    'color': '',
                }
            }
            mock_json.return_value = {'features': [feature1, feature2]}
            pipelines = Pipelines()
            pipelines.update_modes(2025)

            # Year 2025: first pipeline (2020) should be H2, second (2030) should not
            assert len(pipelines.modes) == 2
            assert pipelines.modes[0] == 'H2'
            assert feature1['properties']['color'] == 'limegreen'
            # Second feature should not have been updated
            assert feature2['properties']['color'] == ''
