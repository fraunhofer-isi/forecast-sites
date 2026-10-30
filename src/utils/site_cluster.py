# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import argparse
import logging
import sqlite3

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

EARTH_RADIUS_KM = 6371.0088
TEN = 10


def first_digit(n: int) -> int:
    # Returns the first digit of a positive integer n
    n = abs(int(n))
    while n >= TEN:
        n //= TEN
    return n


def ensure_group_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "group" (
            id_group INTEGER PRIMARY KEY AUTOINCREMENT,
            branch INTEGER NOT NULL,
            id_region INTEGER NOT NULL,
            description TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS group_site (
            id_group INTEGER NOT NULL,
            id_site INTEGER NOT NULL,
            PRIMARY KEY (id_group, id_site),
            FOREIGN KEY (id_group) REFERENCES "group"(id_group),
            FOREIGN KEY (id_site) REFERENCES site(id)
        );
    """)
    cur.execute('CREATE INDEX IF NOT EXISTS idx_group_branch_region ON "group"(branch, id_region);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_group_site_site ON group_site(id_site);')
    conn.commit()


def load_data(
    conn: sqlite3.Connection,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    site = pd.read_sql_query('SELECT id AS id_site, latitude, longitude, id_region FROM site', conn)
    pu = pd.read_sql_query('SELECT id AS id_production_unit, id_site FROM production_unit', conn)
    map_df = pd.read_sql_query(
        'SELECT id_production_unit, id_product FROM production_unit_product_mapping',
        conn,
    )
    return site, pu, map_df


def build_site_branches(_site: pd.DataFrame, pu: pd.DataFrame, map_df: pd.DataFrame) -> pd.DataFrame:
    # Join: mapping -> PU -> Site
    m = map_df.merge(pu, on='id_production_unit', how='inner')
    m['branch'] = m['id_product'].apply(first_digit)
    # Get distinct (site, branch) pairs
    sb = m[['id_site', 'branch']].drop_duplicates()
    return sb


def dbscan_haversine_cluster(coords_deg: np.ndarray, eps_km: float, min_samples: int) -> np.ndarray:
    # coords_deg: array of [lat, lon] in degrees
    coords_rad = np.radians(coords_deg)
    eps_rad = eps_km / EARTH_RADIUS_KM
    model = DBSCAN(eps=eps_rad, min_samples=min_samples, metric='haversine')
    labels = model.fit_predict(coords_rad)
    return labels


def describe_cluster(site_ids: list[int], coords_deg: np.ndarray) -> str:
    lat_mean = float(coords_deg[:, 0].mean())
    lon_mean = float(coords_deg[:, 1].mean())
    site_list = ','.join(map(str, sorted(site_ids)))
    return f'sites={site_list}; centroid=({lat_mean:.5f},{lon_mean:.5f}); count={len(site_ids)}'


def cluster_and_write(conn: sqlite3.Connection, eps_km: float = 50.0, min_samples: int = 3) -> dict[str, int]:
    ensure_group_tables(conn)
    site, pu, map_df = load_data(conn)
    sb = build_site_branches(site, pu, map_df)

    site_b = site.merge(sb, on='id_site', how='inner')

    summary = {'groups_created': 0, 'sites_assigned': 0, 'noise_sites': 0}

    cur = conn.cursor()
    for (region, branch), df in site_b.groupby(['id_region', 'branch']):
        if df.empty:
            continue
        coords = df[['latitude', 'longitude']].to_numpy(dtype=float)
        labels = dbscan_haversine_cluster(coords, eps_km=eps_km, min_samples=min_samples)

        df_labeled = df.assign(cluster_label=labels)
        noise_count = int((labels == -1).sum())
        summary['noise_sites'] += noise_count

        for _, cdf in df_labeled[df_labeled['cluster_label'] != -1].groupby('cluster_label'):
            site_ids = cdf['id_site'].tolist()
            coords_c = cdf[['latitude', 'longitude']].to_numpy(dtype=float)
            desc = describe_cluster(site_ids, coords_c)

            cur.execute(
                'INSERT INTO "group"(branch, id_region, description) VALUES (?, ?, ?)',
                (int(branch), int(region), desc),
            )
            id_group = cur.lastrowid

            cur.executemany(
                'INSERT OR IGNORE INTO group_site(id_group, id_site) VALUES (?, ?)',
                [(id_group, int(sid)) for sid in site_ids],
            )
            summary['groups_created'] += 1
            summary['sites_assigned'] += len(site_ids)

        conn.commit()

    return summary


def ensure_process_branch_column_and_fill(conn: sqlite3.Connection) -> int:
    """
    Add processes.branch_id (INTEGER) if it does not exist

    and fill it with the first digit of processes.id_process.
    Return the number of updated rows.

    """
    cur = conn.cursor()

    cur.execute('PRAGMA table_info(processes);')
    cols = [r[1].lower() for r in cur.fetchall()]
    if 'branch_id' not in cols:
        cur.execute('ALTER TABLE processes ADD COLUMN branch_id INTEGER;')
        conn.commit()

    cur.execute("""
        UPDATE processes
        SET branch_id = CAST(SUBSTR(CAST(id_process AS TEXT), 1, 1) AS INTEGER)
        WHERE branch_id IS NULL;
    """)
    conn.commit()

    cur.execute('SELECT COUNT(*) FROM processes WHERE branch_id IS NOT NULL;')
    count = cur.fetchone()[0]
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cluster sites of an input SQLite database into groups.')
    parser.add_argument('database_path', help='Path to the input SQLite database')
    parser.add_argument('--eps-km', type=float, default=200.0)
    parser.add_argument('--min-samples', type=int, default=3)
    arguments = parser.parse_args()

    conn = sqlite3.connect(arguments.database_path)
    try:
        ensure_process_branch_column_and_fill(conn)
        result = cluster_and_write(conn, eps_km=arguments.eps_km, min_samples=arguments.min_samples)
        logging.info('Done.')
        logging.info(result)
    finally:
        conn.close()
