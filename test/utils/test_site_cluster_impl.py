# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import runpy
import sqlite3
import sys
from pathlib import Path

import pandas as pd

from utils import site_cluster


class RecordingConnection:
    def __init__(self, connection, calls):
        self._connection = connection
        self._calls = calls

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def close(self):
        self._calls.append('close')
        self._connection.close()


def test_cluster_and_write_skips_empty_group_frames(monkeypatch):
    conn = sqlite3.connect(':memory:')
    site = pd.DataFrame([{'id_site': 1, 'latitude': 52.5, 'longitude': 13.4, 'id_region': 7}])
    production_units = pd.DataFrame([{'id_production_unit': 10, 'id_site': 1}])
    mappings = pd.DataFrame([{'id_production_unit': 10, 'id_product': 101}])

    monkeypatch.setattr(site_cluster, 'load_data', lambda _conn: (site, production_units, mappings))
    monkeypatch.setattr(
        pd.DataFrame,
        'groupby',
        lambda self, _keys: [((7, 1), self.iloc[0:0])],
    )

    result = site_cluster.cluster_and_write(conn)

    assert result == {'groups_created': 0, 'sites_assigned': 0, 'noise_sites': 0}
    conn.close()


def test_module_main_runs_cluster_workflow_and_closes_connection(monkeypatch, tmp_path):
    calls = []
    database_path = tmp_path / 'site_cluster.sqlite'
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE processes (id_process INTEGER PRIMARY KEY, name TEXT)')
    cursor.execute('INSERT INTO processes(id_process, name) VALUES (101, "proc")')
    cursor.execute('CREATE TABLE site (id INTEGER, latitude REAL, longitude REAL, id_region INTEGER)')
    cursor.execute('CREATE TABLE production_unit (id INTEGER, id_site INTEGER)')
    cursor.execute('CREATE TABLE production_unit_product_mapping (id_production_unit INTEGER, id_product INTEGER)')
    connection.commit()
    connection.close()
    original_connect = sqlite3.connect

    monkeypatch.setattr(
        site_cluster.sqlite3,
        'connect',
        lambda path: calls.append(('connect', path)) or RecordingConnection(original_connect(database_path), calls),
    )
    monkeypatch.setattr(site_cluster.logging, 'info', lambda message: calls.append(('info', message)))
    # The module reads its arguments from the command line, so pytest's own argv must not leak in.
    monkeypatch.setattr(sys, 'argv', ['site_cluster.py', str(database_path)])

    runpy.run_path(str(Path(site_cluster.__file__)), run_name='__main__')

    assert calls[0][0] == 'connect'
    assert ('info', 'Done.') in calls
    assert any(call == ('info', {'groups_created': 0, 'sites_assigned': 0, 'noise_sites': 0}) for call in calls)
    assert calls[-1] == 'close'
