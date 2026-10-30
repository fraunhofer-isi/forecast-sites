# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import runpy
import sqlite3

import pytest

from input import sqlite_to_csv as sqlite_module
from input.sqlite_to_csv import (
    _check_if_database_exists,
    _create_output_directory_if_not_exists,
    _export_tables_as_csv,
    _fetch_table_names,
    sqlite_to_csv,
)


def test_fetch_table_names_excludes_sqlite_internal_tables():
    connection = sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE foo(id INTEGER)')
    connection.execute('CREATE TABLE bar(id INTEGER)')

    result = _fetch_table_names(connection)

    assert result == ['bar', 'foo']

    connection.close()


def test_check_if_database_exists_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match='SQLite database not found'):
        _check_if_database_exists(tmp_path / 'missing.sqlite')


def test_create_output_directory_if_not_exists_creates_nested_directory(tmp_path):
    output_directory = tmp_path / 'nested' / 'csv'

    _create_output_directory_if_not_exists(output_directory)

    assert output_directory.is_dir()


def test_export_tables_as_csv_writes_rows_and_replaces_existing_file(tmp_path):
    database_path = tmp_path / 'data.sqlite'
    output_directory = tmp_path / 'csv'
    output_directory.mkdir()
    (output_directory / 'foo.csv').write_text('stale\n', encoding='utf-8')
    connection = sqlite3.connect(database_path)
    connection.execute('CREATE TABLE foo(id INTEGER, name TEXT)')
    connection.execute("INSERT INTO foo VALUES (1, 'North')")
    connection.commit()

    _export_tables_as_csv(connection, ['foo'], output_directory)

    contents = (output_directory / 'foo.csv').read_text(encoding='utf-8').splitlines()
    assert contents == ['id,name', '1,North']
    connection.close()


def test_sqlite_to_csv_exports_all_tables(tmp_path):
    database_path = tmp_path / 'data.sqlite'
    output_directory = tmp_path / 'csv'
    connection = sqlite3.connect(database_path)
    connection.execute('CREATE TABLE foo(id INTEGER, name TEXT)')
    connection.execute('CREATE TABLE bar(id INTEGER, value REAL)')
    connection.execute("INSERT INTO foo VALUES (1, 'North')")
    connection.execute('INSERT INTO bar VALUES (2, 3.5)')
    connection.commit()
    connection.close()

    sqlite_to_csv(str(database_path), str(output_directory))

    assert (output_directory / 'bar.csv').read_text(encoding='utf-8').splitlines() == ['id,value', '2,3.5']
    assert (output_directory / 'foo.csv').read_text(encoding='utf-8').splitlines() == ['id,name', '1,North']


def test_main_uses_default_paths(monkeypatch):
    observed = []
    monkeypatch.setattr(
        sqlite_module,
        'sqlite_to_csv',
        lambda database_file, output_directory: observed.append((database_file, output_directory)),
    )

    sqlite_module.main()

    assert observed == [('./resources/input/por_paper_3scenarios.sqlite', './resources/input/por')]


def test_module_main_guard_executes_main(monkeypatch):
    with pytest.raises(FileNotFoundError, match='SQLite database not found'):
        runpy.run_path(sqlite_module.__file__, run_name='__main__')
