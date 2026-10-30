# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for product_route_share_export error handling."""

import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from result.product_route_share_export import export_product_route_shares


class TestProductRouteShareExportMissingDatabase(unittest.TestCase):
    """Test export_product_route_shares with missing database."""

    def test_export_with_missing_database(self):
        """Test export_product_route_shares raises FileNotFoundError when database missing."""
        with TemporaryDirectory() as tmpdir:
            simulation_options = {
                'start_year': 2020,
                'end_year': 2030,
                'year_increment': 1,
                'output_directory': tmpdir,
            }

            with pytest.raises(FileNotFoundError) as context:
                export_product_route_shares(1, simulation_options)

            assert 'output.sqlite' in str(context.value)


class TestProductRouteShareExportMissingResultTables(unittest.TestCase):
    """Test export_product_route_shares when output.sqlite exists but has no result tables."""

    def test_export_with_missing_result_tables(self):
        """Test export_product_route_shares raises RuntimeError naming the missing table.

        This is distinct from the missing-database case above: the file exists (so the
        FileNotFoundError guard passes), but a simulation never ran against it, so none of
        the result tables that _read_chain_tables depends on exist yet.
        """
        with TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / 'output.sqlite'
            sqlite3.connect(database_path).close()  # file exists, but has zero tables

            simulation_options = {
                'start_year': 2020,
                'end_year': 2030,
                'year_increment': 1,
                'output_directory': tmpdir,
            }

            with pytest.raises(RuntimeError, match='process_product_production_in_t'):
                export_product_route_shares(1, simulation_options)
