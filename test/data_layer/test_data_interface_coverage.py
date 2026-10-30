# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Targeted unit tests to achieve 100% coverage for data_interface.py
Targeting missing lines 263-265 and 281-283
- Lines 263-265: if len(df) > 0 branch in _read_production_units_by_sites
- Lines 281-283: else branch for missing products in _read_production_unit_product_mapping
"""

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from data_layer.data_interface import DataInterface


class TestReadProductionUnitsBySites:
    """Test _read_production_units_by_sites method focusing on line 263 (len(df) > 0 branch)."""

    def test_read_production_units_by_sites_with_empty_dataframe(self):
        """Test when query returns empty DataFrame for a site."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            # Create production_unit table
            pd.DataFrame(
                {
                    'id_production_unit': [1, 2, 3],
                    'id_site': [10, 20, 30],
                    'name': ['Unit1', 'Unit2', 'Unit3'],
                }
            ).to_sql('production_unit', conn, if_exists='replace', index=False)

            conn.close()

            # Now test with site_ids that don't have production units
            conn = sqlite3.connect(str(db_path))
            site_ids = [100, 200]  # Sites without any production units

            site_map, production_unit_ids = DataInterface._read_production_units_by_sites(conn, site_ids)

            # Both sites should be processed but site_map should be empty
            assert isinstance(site_map, dict)
            assert len(site_map) == 0  # No sites found
            assert isinstance(production_unit_ids, list)
            assert len(production_unit_ids) == 0  # No production units found

            conn.close()

    def test_read_production_units_by_sites_with_non_empty_dataframe(self):
        """Test line 263: when len(df) > 0 is True (non-empty DataFrame)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            # Create production_unit table with data
            production_units = pd.DataFrame(
                {
                    'id_production_unit': [1, 2, 3],
                    'id_site': [10, 10, 20],
                    'name': ['Unit1', 'Unit2', 'Unit3'],
                }
            )
            production_units.to_sql('production_unit', conn, if_exists='replace', index=False)

            conn.close()

            # Test with site_ids that have production units
            conn = sqlite3.connect(str(db_path))
            site_ids = [10, 20]

            site_map, production_unit_ids = DataInterface._read_production_units_by_sites(conn, site_ids)

            # Lines 263-265 should execute: site_map[id_site] = df and production_unit_id_set.update()
            assert len(site_map) == 2  # Both sites should be in map
            assert 10 in site_map
            assert 20 in site_map

            # Check that the dataframes are stored correctly
            assert len(site_map[10]) == 2  # Site 10 has 2 units
            assert len(site_map[20]) == 1  # Site 20 has 1 unit

            # Check production unit IDs are collected
            assert len(production_unit_ids) == 3
            assert set(production_unit_ids) == {1, 2, 3}

            conn.close()

    def test_read_production_units_by_sites_mixed_empty_and_non_empty(self):
        """Test with mix of sites with and without production units."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            # Create production_unit table
            pd.DataFrame(
                {
                    'id_production_unit': [1, 2],
                    'id_site': [10, 10],
                    'name': ['Unit1', 'Unit2'],
                }
            ).to_sql('production_unit', conn, if_exists='replace', index=False)

            conn.close()

            conn = sqlite3.connect(str(db_path))
            site_ids = [10, 20, 30]  # Site 10 has units, 20 and 30 don't

            site_map, production_unit_ids = DataInterface._read_production_units_by_sites(conn, site_ids)

            # Only site 10 should be in map (lines 263-265 trigger)
            assert len(site_map) == 1
            assert 10 in site_map
            assert 20 not in site_map
            assert 30 not in site_map

            # Production unit IDs should only have units from site 10
            assert len(production_unit_ids) == 2
            assert set(production_unit_ids) == {1, 2}

            conn.close()

    def test_read_production_units_by_sites_single_unit_per_site(self):
        """Test line 263 with exactly one production unit per site."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            pd.DataFrame(
                {
                    'id_production_unit': [1, 2, 3],
                    'id_site': [10, 20, 30],
                    'name': ['Unit1', 'Unit2', 'Unit3'],
                }
            ).to_sql('production_unit', conn, if_exists='replace', index=False)

            conn.close()

            conn = sqlite3.connect(str(db_path))
            site_ids = [10, 20, 30]

            site_map, production_unit_ids = DataInterface._read_production_units_by_sites(conn, site_ids)

            # All sites should be in map with exactly 1 unit each (lines 263-265)
            assert len(site_map) == 3
            for site_id in site_ids:
                assert site_id in site_map
                assert len(site_map[site_id]) == 1

            assert len(production_unit_ids) == 3

            conn.close()


class TestReadProductionUnitProductMapping:
    """Test _read_production_unit_product_mapping focusing on lines 281-283 (error case)."""

    def test_read_production_unit_product_mapping_no_filter_returns_data(self):
        """Test when no product filter is applied and data exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            # Create production_unit_product_mapping table
            pd.DataFrame(
                {
                    'id_production_unit': [1, 2, 3],
                    'id_product': [10, 20, 30],
                    'amount': [100, 200, 300],
                }
            ).to_sql('production_unit_product_mapping_in_t', conn, if_exists='replace', index=False)

            conn.close()

            conn = sqlite3.connect(str(db_path))
            id_product_filter = []  # No filtering

            result = DataInterface._read_production_unit_product_mapping(conn, id_product_filter)

            assert len(result) == 3
            assert list(result['id_production_unit']) == [1, 2, 3]

            conn.close()

    def test_read_production_unit_product_mapping_with_filter_returns_data(self):
        """Test when product filter is applied and matching data exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            pd.DataFrame(
                {
                    'id_production_unit': [1, 2, 3, 4],
                    'id_product': [10, 20, 10, 30],
                    'amount': [100, 200, 150, 300],
                }
            ).to_sql('production_unit_product_mapping_in_t', conn, if_exists='replace', index=False)

            conn.close()

            conn = sqlite3.connect(str(db_path))
            id_product_filter = [10]  # Filter for product 10

            result = DataInterface._read_production_unit_product_mapping(conn, id_product_filter)

            assert len(result) == 2  # Only units with product 10
            assert 10 in result['id_product'].to_numpy()

            conn.close()

    def test_read_production_unit_product_mapping_no_data_raises_error(self):
        """Test lines 281-283: when no data is found (else branch)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            # Create empty table
            pd.DataFrame(
                {
                    'id_production_unit': pd.Series(dtype='int64'),
                    'id_product': pd.Series(dtype='int64'),
                    'amount': pd.Series(dtype='float64'),
                }
            ).to_sql('production_unit_product_mapping_in_t', conn, if_exists='replace', index=False)

            conn.close()

            conn = sqlite3.connect(str(db_path))
            id_product_filter = []

            # Lines 279-283: Should raise ValueError with message
            with pytest.raises(ValueError, match='No production units found'):
                DataInterface._read_production_unit_product_mapping(conn, id_product_filter)

            conn.close()

    def test_read_production_unit_product_mapping_filtered_no_data_raises_error(self):
        """Test line 282: error message includes product filter info when filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'

            # Create table with data in a separate connection
            conn = sqlite3.connect(str(db_path))
            try:
                # Create table with data but for different products
                pd.DataFrame(
                    {
                        'id_production_unit': [1, 2],
                        'id_product': [100, 100],
                        'amount': [100, 200],
                    }
                ).to_sql('production_unit_product_mapping_in_t', conn, if_exists='replace', index=False)
            finally:
                conn.close()

            # Open new connection for actual test
            conn = sqlite3.connect(str(db_path))
            try:
                id_product_filter = [10, 20]  # Products not in table

                # Lines 281-282: Error message should include product filter info
                with pytest.raises(ValueError, match='No production units found') as exc_info:
                    DataInterface._read_production_unit_product_mapping(conn, id_product_filter)

                error_message = str(exc_info.value)
                assert 'No production units found' in error_message
                assert 'product_ids' in error_message  # Line 282 adds this
            finally:
                conn.close()

    def test_read_production_unit_product_mapping_partial_match_with_filter(self):
        """Test that filter correctly matches subset of products."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            pd.DataFrame(
                {
                    'id_production_unit': [1, 2, 3, 4, 5],
                    'id_product': [10, 20, 30, 20, 10],
                    'amount': [100, 200, 300, 250, 150],
                }
            ).to_sql('production_unit_product_mapping_in_t', conn, if_exists='replace', index=False)

            conn.close()

            conn = sqlite3.connect(str(db_path))
            id_product_filter = [10, 20]

            result = DataInterface._read_production_unit_product_mapping(conn, id_product_filter)

            # Should return only units with products 10 or 20
            assert len(result) == 4
            assert set(result['id_product'].unique()) == {10, 20}
            assert set(result['id_production_unit']) == {1, 2, 4, 5}

            conn.close()

    def test_read_production_unit_product_mapping_empty_filter_gets_all(self):
        """Test that empty filter returns all data (line 279-280)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.sqlite'
            conn = sqlite3.connect(str(db_path))

            pd.DataFrame(
                {
                    'id_production_unit': [1, 2, 3],
                    'id_product': [10, 20, 30],
                    'amount': [100, 200, 300],
                }
            ).to_sql('production_unit_product_mapping_in_t', conn, if_exists='replace', index=False)

            conn.close()

            conn = sqlite3.connect(str(db_path))
            id_product_filter = []  # Empty filter

            result = DataInterface._read_production_unit_product_mapping(conn, id_product_filter)

            # Should return all data
            assert len(result) == 3

            conn.close()
