# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import sqlite3

import numpy as np
import pandas as pd

from utils.site_cluster import (
    build_site_branches,
    cluster_and_write,
    dbscan_haversine_cluster,
    describe_cluster,
    ensure_group_tables,
    ensure_process_branch_column_and_fill,
    first_digit,
    load_data,
)


def test_first_digit_single_digit():
    assert first_digit(5) == 5


def test_first_digit_multi_digit():
    assert first_digit(12345) == 1


def test_first_digit_negative():
    assert first_digit(-987) == 9


def test_first_digit_zero():
    assert first_digit(0) == 0


def test_dbscan_haversine_cluster_single_cluster():
    # Create three points very close together (should form one cluster)
    coords_deg = np.array(
        [
            [52.0, 13.0],
            [52.001, 13.001],
            [52.002, 13.002],
        ]
    )
    labels = dbscan_haversine_cluster(coords_deg, eps_km=50.0, min_samples=2)
    # All points should be in the same cluster (not noise, labeled 0)
    assert len(set(labels[labels != -1])) <= 1


def test_dbscan_haversine_cluster_noise():
    # Create points very far apart (should be noise)
    coords_deg = np.array(
        [
            [0.0, 0.0],
            [45.0, 45.0],
        ]
    )
    labels = dbscan_haversine_cluster(coords_deg, eps_km=50.0, min_samples=2)
    # Both should be noise (labeled -1)
    assert np.all(labels == -1)


def test_describe_cluster_single_site():
    site_ids = [1]
    coords = np.array([[52.5, 13.4]])
    description = describe_cluster(site_ids, coords)
    assert 'sites=1' in description
    assert 'count=1' in description


def test_describe_cluster_multiple_sites():
    site_ids = [1, 2, 3]
    coords = np.array(
        [
            [52.5, 13.4],
            [52.6, 13.5],
            [52.7, 13.6],
        ]
    )
    description = describe_cluster(site_ids, coords)
    assert 'sites=1,2,3' in description
    assert 'count=3' in description
    assert 'centroid=' in description


def test_build_site_branches():
    site_df = pd.DataFrame({'id_site': [1, 2, 3]})
    pu_df = pd.DataFrame(
        {
            'id_production_unit': [10, 11, 12],
            'id_site': [1, 2, 3],
        }
    )
    map_df = pd.DataFrame(
        {
            'id_production_unit': [10, 11, 12],
            'id_product': [101, 201, 301],  # first digits: 1, 2, 3
        }
    )

    result = build_site_branches(site_df, pu_df, map_df)

    # Should have 3 rows with distinct (site, branch) combinations
    assert len(result) == 3
    assert set(result['branch'].values) == {1, 2, 3}
    assert set(result['id_site'].values) == {1, 2, 3}


def test_build_site_branches_duplicate_removal():
    site_df = pd.DataFrame({'id_site': [1, 1]})
    pu_df = pd.DataFrame(
        {
            'id_production_unit': [10, 11],
            'id_site': [1, 1],
        }
    )
    map_df = pd.DataFrame(
        {
            'id_production_unit': [10, 11],
            'id_product': [101, 102],  # both have first digit 1
        }
    )

    result = build_site_branches(site_df, pu_df, map_df)

    # Should have 1 row due to deduplication of (site=1, branch=1)
    assert len(result) == 1
    assert result.iloc[0]['id_site'] == 1
    assert result.iloc[0]['branch'] == 1


def test_ensure_group_tables_creates_tables_and_indexes():
    conn = sqlite3.connect(':memory:')

    ensure_group_tables(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group'")
    assert cursor.fetchone() == ('group',)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_site'")
    assert cursor.fetchone() == ('group_site',)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_group_branch_region'")
    assert cursor.fetchone() == ('idx_group_branch_region',)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_group_site_site'")
    assert cursor.fetchone() == ('idx_group_site_site',)
    conn.close()


def test_load_data_reads_expected_tables():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE site (id INTEGER, latitude REAL, longitude REAL, id_region INTEGER)')
    cursor.execute('CREATE TABLE production_unit (id INTEGER, id_site INTEGER)')
    cursor.execute('CREATE TABLE production_unit_product_mapping (id_production_unit INTEGER, id_product INTEGER)')
    cursor.execute('INSERT INTO site VALUES (1, 52.5, 13.4, 7)')
    cursor.execute('INSERT INTO production_unit VALUES (10, 1)')
    cursor.execute('INSERT INTO production_unit_product_mapping VALUES (10, 101)')
    conn.commit()

    site, production_units, mappings = load_data(conn)

    assert site.to_dict('records') == [{'id_site': 1, 'latitude': 52.5, 'longitude': 13.4, 'id_region': 7}]
    assert production_units.to_dict('records') == [{'id_production_unit': 10, 'id_site': 1}]
    assert mappings.to_dict('records') == [{'id_production_unit': 10, 'id_product': 101}]
    conn.close()


def test_cluster_and_write_returns_zero_summary_when_no_group_candidates(monkeypatch):
    conn = sqlite3.connect(':memory:')
    monkeypatch.setattr(
        'utils.site_cluster.load_data',
        lambda _conn: (
            pd.DataFrame(columns=['id_site', 'latitude', 'longitude', 'id_region']),
            pd.DataFrame(columns=['id_production_unit', 'id_site']),
            pd.DataFrame(columns=['id_production_unit', 'id_product']),
        ),
    )

    result = cluster_and_write(conn)

    assert result == {'groups_created': 0, 'sites_assigned': 0, 'noise_sites': 0}
    conn.close()


def test_cluster_and_write_inserts_group_and_memberships(monkeypatch):
    conn = sqlite3.connect(':memory:')
    site = pd.DataFrame(
        [
            {'id_site': 1, 'latitude': 52.5, 'longitude': 13.4, 'id_region': 7},
            {'id_site': 2, 'latitude': 52.6, 'longitude': 13.5, 'id_region': 7},
        ]
    )
    production_units = pd.DataFrame(
        [
            {'id_production_unit': 10, 'id_site': 1},
            {'id_production_unit': 11, 'id_site': 2},
        ]
    )
    mappings = pd.DataFrame(
        [
            {'id_production_unit': 10, 'id_product': 101},
            {'id_production_unit': 11, 'id_product': 101},
        ]
    )
    monkeypatch.setattr('utils.site_cluster.load_data', lambda _conn: (site, production_units, mappings))
    monkeypatch.setattr('utils.site_cluster.dbscan_haversine_cluster', lambda coords, eps_km, min_samples: np.array([0, 0]))

    result = cluster_and_write(conn)

    assert result == {'groups_created': 1, 'sites_assigned': 2, 'noise_sites': 0}
    cursor = conn.cursor()
    cursor.execute('SELECT branch, id_region, description FROM "group"')
    branch, region, description = cursor.fetchone()
    assert (branch, region) == (1, 7)
    assert 'sites=1,2' in description
    cursor.execute('SELECT id_site FROM group_site ORDER BY id_site')
    assert cursor.fetchall() == [(1,), (2,)]
    conn.close()


def test_cluster_and_write_counts_noise_sites(monkeypatch):
    conn = sqlite3.connect(':memory:')
    site = pd.DataFrame(
        [
            {'id_site': 1, 'latitude': 52.5, 'longitude': 13.4, 'id_region': 7},
            {'id_site': 2, 'latitude': 52.6, 'longitude': 13.5, 'id_region': 7},
        ]
    )
    production_units = pd.DataFrame(
        [
            {'id_production_unit': 10, 'id_site': 1},
            {'id_production_unit': 11, 'id_site': 2},
        ]
    )
    mappings = pd.DataFrame(
        [
            {'id_production_unit': 10, 'id_product': 101},
            {'id_production_unit': 11, 'id_product': 101},
        ]
    )
    monkeypatch.setattr('utils.site_cluster.load_data', lambda _conn: (site, production_units, mappings))
    monkeypatch.setattr('utils.site_cluster.dbscan_haversine_cluster', lambda coords, eps_km, min_samples: np.array([0, -1]))

    result = cluster_and_write(conn)

    assert result == {'groups_created': 1, 'sites_assigned': 1, 'noise_sites': 1}
    conn.close()


def test_ensure_process_branch_column_and_fill_adds_and_populates_branch_id():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE processes (id_process INTEGER PRIMARY KEY, name TEXT)')
    cursor.executemany(
        'INSERT INTO processes(id_process, name) VALUES (?, ?)',
        [(123, 'a'), (245, 'b')],
    )
    conn.commit()

    count = ensure_process_branch_column_and_fill(conn)

    assert count == 2
    cursor.execute('SELECT id_process, branch_id FROM processes ORDER BY id_process')
    assert cursor.fetchall() == [(123, 1), (245, 2)]
    conn.close()


def test_ensure_process_branch_column_and_fill_keeps_existing_column():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE processes (id_process INTEGER PRIMARY KEY, branch_id INTEGER)')
    cursor.executemany(
        'INSERT INTO processes(id_process, branch_id) VALUES (?, ?)',
        [(123, None), (245, 9)],
    )
    conn.commit()

    count = ensure_process_branch_column_and_fill(conn)

    assert count == 2
    cursor.execute('SELECT id_process, branch_id FROM processes ORDER BY id_process')
    assert cursor.fetchall() == [(123, 1), (245, 9)]
    conn.close()
