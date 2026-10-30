# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Integration tests for product_route_share_export covering lines 105-149, 189-396, 419-421."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from result.product_route_share_export import (
    AMMONIA_PRODUCT_ID,
    CHAIN_TABLE_NAMES,
    _build_lhv_map,
    _merge_export_table,
    _read_chain_tables,
    _save_iamc_production_table,
    _save_wide_table,
    export_product_route_shares,
)


def _create_test_database(db_path):
    """Create a minimal SQLite database with required tables for testing."""
    conn = sqlite3.connect(db_path)
    try:
        # Create chain tables with minimal data
        for table_name in CHAIN_TABLE_NAMES:
            conn.execute(f"""
                CREATE TABLE `{table_name}` (
                    id_scenario INTEGER,
                    id_region INTEGER,
                    id_process INTEGER,
                    id_product INTEGER DEFAULT 0,
                    id_by_product INTEGER DEFAULT 0,
                    id_energy_carrier INTEGER DEFAULT 0,
                    Y2020 REAL DEFAULT 0,
                    Y2025 REAL DEFAULT 0
                )
            """)

        # Insert production data for ammonia (product 501)
        conn.execute("""
            INSERT INTO process_product_production_in_t
            (id_scenario, id_region, id_process, id_product, Y2020, Y2025)
            VALUES (1, 1, 5120, 501, 100.0, 120.0)
        """)

        # Create id_region table
        conn.execute('CREATE TABLE id_region (id INTEGER, name TEXT)')
        conn.execute("INSERT INTO id_region (id, name) VALUES (1, 'Germany')")

        # Create id_scenario table
        conn.execute('CREATE TABLE id_scenario (id INTEGER, name TEXT)')
        conn.execute("INSERT INTO id_scenario (id, name) VALUES (1, 'Base')")

        conn.commit()
    finally:
        conn.close()


class TestExportProductRouteSharesIntegration(unittest.TestCase):
    """Integration test for export_product_route_shares (lines 105-149)."""

    def test_export_product_route_shares_full_flow(self):
        """Test the full export flow with a minimal database."""
        import shutil

        output_path = Path(tempfile.mkdtemp())
        try:
            db_path = output_path / 'output.sqlite'
            _create_test_database(db_path)

            simulation_options = {
                'start_year': 2020,
                'end_year': 2025,
                'year_increment': 5,
                'output_directory': output_path,
            }

            export_product_route_shares(1, simulation_options)

            # Verify output files were created
            assert (output_path / 'product_route_production_by_region_in_t.xlsx').exists()
            assert (output_path / 'product_route_share_by_region_in_percent.xlsx').exists()
        finally:
            shutil.rmtree(output_path, ignore_errors=True)

    def test_read_chain_tables_from_database(self):
        """Test reading all chain tables from SQLite database (lines 286-293)."""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / 'test.sqlite'
        _create_test_database(db_path)

        tables = _read_chain_tables(db_path)

        assert 'process_product_production_in_t' in tables
        assert 'id_region' in tables
        assert 'id_scenario' in tables

    def test_build_lhv_map_with_year_column(self):
        """Test building LHV map with Y2020 column (lines 340-355)."""
        lhv_df = pd.DataFrame(
            {
                'id_energy_carrier': [1, 2],
                'Y2020': [40.0, 35.0],
            }
        )

        result = _build_lhv_map(lhv_df, 2020)

        assert result == {1: 40.0, 2: 35.0}

    def test_build_lhv_map_with_nan_value(self):
        """Test building LHV map with NaN values uses default."""
        lhv_df = pd.DataFrame(
            {
                'id_energy_carrier': [1],
                'Y2020': [float('nan')],
            }
        )

        result = _build_lhv_map(lhv_df, 2020)

        assert result[1] == 40.0  # DEFAULT_LHV_GJ_PER_T

    def test_save_wide_table_with_data(self):
        """Test saving wide table with actual data (lines 365-378)."""
        output_path = Path(tempfile.mkdtemp())
        db_path = output_path / 'output.sqlite'
        sqlite3.connect(db_path).close()

        rows = [
            {'scenario': 'Base', 'region': 'DE', 'product': 'Ammonia', 'route': 'SMR', 'year': 2020, 'share_in_percent': 50.0},
            {'scenario': 'Base', 'region': 'DE', 'product': 'Ammonia', 'route': 'SMR', 'year': 2025, 'share_in_percent': 40.0},
        ]

        _save_wide_table(
            rows,
            output_path,
            'test_table',
            'share_in_percent',
            index_columns=['scenario', 'region', 'product', 'route'],
        )

        assert (output_path / 'test_table.xlsx').exists()

    def test_save_wide_table_empty(self):
        """Test saving wide table with empty data (lines 366-368)."""
        output_path = Path(tempfile.mkdtemp())
        db_path = output_path / 'output.sqlite'
        sqlite3.connect(db_path).close()

        _save_wide_table(
            [],
            output_path,
            'empty_table',
            'share_in_percent',
            index_columns=['scenario', 'region', 'product', 'route'],
        )

        assert (output_path / 'empty_table.xlsx').exists()

    def test_save_iamc_production_table(self):
        """Test saving IAMC production table (lines 387-396)."""
        output_path = Path(tempfile.mkdtemp())
        db_path = output_path / 'output.sqlite'
        sqlite3.connect(db_path).close()

        rows = [
            {'region': 'Germany', 'product': 'Ammonia', 'route': 'SMR', 'year': 2020, 'production_in_t': 1000000.0},
        ]

        _save_iamc_production_table(rows, output_path, 'test_iamc', 'Base')

        assert (output_path / 'test_iamc.xlsx').exists()

    def test_merge_with_existing_empty_table(self):
        """Test merge when existing table is empty (line 419)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / 'test.sqlite'
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test_merge (scenario TEXT, value REAL)')
            conn.commit()

            new_df = pd.DataFrame({'scenario': ['Base'], 'value': [1.0]})
            result = _merge_export_table(conn, 'test_merge', new_df, ['scenario'])

            conn.close()
            assert len(result) == 1

    def test_merge_with_new_empty_df(self):
        """Test merge when new DataFrame is empty (line 421)."""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / 'test.sqlite'
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE test_merge (scenario TEXT, value REAL)')
        conn.execute("INSERT INTO test_merge VALUES ('Base', 2.0)")
        conn.commit()

        new_df = pd.DataFrame({'scenario': [], 'value': []})
        result = _merge_export_table(conn, 'test_merge', new_df, ['scenario'])

        conn.close()
        assert len(result) == 1

    def test_route_basis_for_chain_non_ammonia_product(self):
        """Branch 239->246: product_id not in {AMMONIA, METHANOL} skips carrier_basis."""
        from result.product_route_share_export import _route_basis_for_chain
        from route_analysis.upstream_chain_builder import UpstreamChain

        chain = UpstreamChain()
        chain.final_product_outputs = [(5120, 999, 100.0)]
        chain.carrier_flows = [(5120, 1, 2, 50.0)]

        result = _route_basis_for_chain(999, chain, {5120})

        assert result == 100.0

    def test_classify_chain_with_purchase_routes(self):
        """Line 217: purchase route bases are added to route_bases."""
        from result.product_route_share_export import _classify_chain_into_routes
        from route_analysis.upstream_chain_builder import UpstreamChain

        chain = UpstreamChain()
        chain.process_ids = set()
        chain.final_product_outputs = [(5120, AMMONIA_PRODUCT_ID, 100.0)]
        chain.carrier_flows = []
        chain.purchased_carrier_flows = [(26, 1, 50.0)]

        result = _classify_chain_into_routes(AMMONIA_PRODUCT_ID, chain)

        assert 'Imported hydrogen-derived' in result

    def test_classify_chain_no_routes_returns_other(self):
        """Lines 220-221: no route bases returns OTHER_ROUTE."""
        from result.product_route_share_export import OTHER_ROUTE, _classify_chain_into_routes
        from route_analysis.upstream_chain_builder import UpstreamChain

        chain = UpstreamChain()
        chain.process_ids = set()
        chain.final_product_outputs = [(9999, AMMONIA_PRODUCT_ID, 100.0)]
        chain.carrier_flows = []
        chain.purchased_carrier_flows = []

        result = _classify_chain_into_routes(AMMONIA_PRODUCT_ID, chain)

        assert OTHER_ROUTE in result
        assert result[OTHER_ROUTE] == 100.0

    def test_classify_chain_tiny_basis_single_route(self):
        """Lines 229-232: single route with zero basis gets all output."""
        from result.product_route_share_export import _classify_chain_into_routes
        from route_analysis.upstream_chain_builder import UpstreamChain

        chain = UpstreamChain()
        # Process 5120 (SMR anchor) is in process_ids but has NO flows
        chain.process_ids = {5120}
        # Final output from a DIFFERENT process (not 5120)
        chain.final_product_outputs = [(9999, AMMONIA_PRODUCT_ID, 100.0)]
        chain.carrier_flows = []
        chain.product_flows = []
        chain.by_product_flows = []
        chain.purchased_carrier_flows = []

        result = _classify_chain_into_routes(AMMONIA_PRODUCT_ID, chain)

        # SMR route matched (5120 in process_ids) but basis is 0
        # total_basis = 0 <= ROUTE_MIN_VALUE, single route → assign all output to it
        assert result['SMR'] == 100.0

    def test_classify_chain_tiny_basis_multiple_routes_returns_other(self):
        """Lines 234-235: multiple routes with zero basis → OTHER gets all output."""
        from result.product_route_share_export import OTHER_ROUTE, _classify_chain_into_routes
        from route_analysis.upstream_chain_builder import UpstreamChain

        chain = UpstreamChain()
        # Both SMR (5120) and SMR+CCS (5130) anchors in process_ids but NO flows
        chain.process_ids = {5120, 5130}
        # Final output from a DIFFERENT process
        chain.final_product_outputs = [(9999, AMMONIA_PRODUCT_ID, 100.0)]
        chain.carrier_flows = []
        chain.product_flows = []
        chain.by_product_flows = []
        chain.purchased_carrier_flows = []

        result = _classify_chain_into_routes(AMMONIA_PRODUCT_ID, chain)

        # Multiple routes matched but all with zero basis → OTHER
        assert result[OTHER_ROUTE] == 100.0

    def test_region_ids_for_export_without_scenario_column(self):
        """Branch 309->311: id_scenario column not present in DataFrame."""
        from result.product_route_share_export import _region_ids_for_export

        # DataFrame without id_scenario column
        product_df = pd.DataFrame(
            {
                'id_product': [AMMONIA_PRODUCT_ID],
                'id_region': [1],
            }
        )
        tables = {'process_product_production_in_t': product_df}

        result = _region_ids_for_export(tables, scenario_id=1)

        # Should return region IDs without filtering by scenario
        assert result == [1]
