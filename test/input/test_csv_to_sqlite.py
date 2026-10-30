# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging
import runpy
import sqlite3
from pathlib import Path

import pandas as pd
import pytest
from test_utils.isi_mock import Mock, patch

from input import csv_to_sqlite as csv_module
from input.csv_to_sqlite import (
    _check_column_names_for_id_table,
    _check_id_names_for_typos,
    _check_if_directory_exists,
    _create_sqlite_id_table,
    _delete_database_if_exists,
    _duplicate_ids,
    _foreign_key_definitions,
    _id_table_names,
    _identify_columns,
    _import_id_table,
    _import_id_tables,
    _import_table,
    _import_tables,
    _read_csv_file_names_from_directory_without_ending,
    _read_table,
    _remaining_table_names,
    csv_to_sqlite,
    main,
)


def test_check_column_names_for_id_table_accepts_id_name_columns():
    df = pd.DataFrame([{'id': 1, 'name': 'foo'}])

    _check_column_names_for_id_table(df)


def test_check_column_names_for_id_table_rejects_unexpected_columns():
    df = pd.DataFrame([{'id': 1, 'label': 'foo'}])

    with pytest.raises(ValueError, match="must have columns 'id' and 'name'"):
        _check_column_names_for_id_table(df)


def test_duplicate_ids_returns_only_duplicates():
    rows = [(1, 'a'), (2, 'b'), (1, 'c'), (3, 'd'), (2, 'e')]

    result = _duplicate_ids(rows)

    assert result == [1, 2]


def test_identify_columns_splits_id_and_value_columns():
    df = pd.DataFrame(columns=['id_region', 'id_process', 'value', 'Y2030'])

    id_columns, value_columns = _identify_columns(df)

    assert id_columns == ['id_region', 'id_process']
    assert value_columns == ['value', 'Y2030']


def test_remaining_table_names_excludes_id_tables():
    result = _remaining_table_names(['id_region', 'id_process', 'foo'], ['id_region', 'id_process'])

    assert result == ['foo']


def test_check_if_directory_exists_accepts_existing_directory(tmp_path):
    _check_if_directory_exists(tmp_path)


def test_check_if_directory_exists_raises_for_missing_directory(tmp_path):
    missing_path = tmp_path / 'missing'

    with pytest.raises(FileNotFoundError, match='Source directory not found'):
        _check_if_directory_exists(missing_path)


def test_delete_database_if_exists_removes_existing_file(tmp_path):
    database_path = tmp_path / 'test.sqlite'
    database_path.write_text('db', encoding='utf-8')

    _delete_database_if_exists(database_path)

    assert not database_path.exists()


def test_delete_database_if_exists_raises_for_directory(tmp_path):
    with pytest.raises(IsADirectoryError, match='found a directory'):
        _delete_database_if_exists(tmp_path)


def test_delete_database_if_exists_wraps_permission_error(monkeypatch, tmp_path):
    database_path = tmp_path / 'test.sqlite'
    database_path.write_text('db', encoding='utf-8')

    monkeypatch.setattr(Path, 'unlink', lambda self: (_ for _ in ()).throw(PermissionError('locked')))

    with pytest.raises(PermissionError, match='Could not delete existing database'):
        _delete_database_if_exists(database_path)


def test_read_csv_file_names_from_directory_without_ending_filters_csv(tmp_path):
    (tmp_path / 'id_region.csv').write_text('id,name\n1,North\n', encoding='utf-8')
    (tmp_path / 'process.csv').write_text('id_process,value\n1,2\n', encoding='utf-8')
    (tmp_path / 'ignore.txt').write_text('x', encoding='utf-8')

    result = sorted(_read_csv_file_names_from_directory_without_ending(tmp_path))

    assert result == ['id_region', 'process']


def test_id_table_names_selects_only_id_prefixed_entries():
    result = _id_table_names(['id_region', 'foo', 'ID_process', 'bar'])

    assert result == ['id_region', 'ID_process']


def test_foreign_key_definitions_include_only_id_columns():
    result = _foreign_key_definitions(['id_region', 'value', 'id_product'])

    assert result == [
        'FOREIGN KEY("id_region") REFERENCES id_region(id) ON DELETE CASCADE ON UPDATE CASCADE',
        'FOREIGN KEY("id_product") REFERENCES id_product(id) ON DELETE CASCADE ON UPDATE CASCADE',
    ]


def test_create_sqlite_id_table_creates_table_and_rows():
    connection = sqlite3.connect(':memory:')
    id_table = pd.DataFrame([{'id': 1, 'name': 'North'}, {'id': 2, 'name': 'South'}])

    _create_sqlite_id_table('id_region', id_table, connection)

    rows = connection.execute('SELECT id, name FROM id_region ORDER BY id').fetchall()
    assert rows == [(1, 'North'), (2, 'South')]
    connection.close()


def test_create_sqlite_id_table_raises_for_duplicate_ids():
    connection = sqlite3.connect(':memory:')
    id_table = pd.DataFrame([{'id': 1, 'name': 'North'}, {'id': 1, 'name': 'South'}])

    with pytest.raises(sqlite3.IntegrityError):
        _create_sqlite_id_table('id_region', id_table, connection)

    connection.close()


def test_create_sqlite_id_table_logs_duplicate_ids_on_integrity_error():
    """Test that duplicate IDs are logged when UNIQUE constraint fails (lines 131-137)."""
    connection = sqlite3.connect(':memory:')
    id_table = pd.DataFrame([{'id': 1, 'name': 'North'}, {'id': 2, 'name': 'South'}, {'id': 1, 'name': 'East'}])

    # Patch logging to capture the exception logging
    with patch(logging.exception) as mock_log:
        with pytest.raises(sqlite3.IntegrityError):
            _create_sqlite_id_table('id_region', id_table, connection)

        # Verify logging.exception was called with expected message containing duplicate ID
        assert mock_log.called
        call_args = mock_log.call_args[0][0]
        assert 'duplicate id values' in call_args
        assert '1' in call_args  # The duplicate ID should be mentioned

    connection.close()


def test_csv_to_sqlite_orchestrates_import_order(tmp_path, monkeypatch):
    source_directory = tmp_path / 'csv'
    source_directory.mkdir()
    database_path = tmp_path / 'out.sqlite'
    (source_directory / 'id_region.csv').write_text('id,name\n1,North\n', encoding='latin-1')
    (source_directory / 'process.csv').write_text('id_process,value\n1,2\n', encoding='latin-1')
    calls = []

    def record_id_tables(table_names, source, connection):
        calls.append(('id', table_names, Path(source).name, isinstance(connection, sqlite3.Connection)))

    def record_tables(table_names, source, connection):
        calls.append(('other', table_names, Path(source).name, isinstance(connection, sqlite3.Connection)))

    monkeypatch.setattr(csv_module, '_import_id_tables', record_id_tables)
    monkeypatch.setattr(csv_module, '_import_tables', record_tables)

    csv_to_sqlite(source_directory, database_path)

    assert calls == [
        ('id', ['id_region'], 'csv', True),
        ('other', ['process'], 'csv', True),
    ]


def test_read_table_reads_latin1_csv(tmp_path):
    source_directory = tmp_path
    file_path = source_directory / 'id_region.csv'
    file_path.write_bytes('id,name\n1,äöü\n'.encode('latin-1'))

    result = _read_table('id_region', source_directory)

    assert result.to_dict('records') == [{'id': 1, 'name': 'äöü'}]


def test_import_id_table_reads_validates_and_creates(monkeypatch):
    id_table = pd.DataFrame([{'id': 1, 'name': 'North'}])
    read_table = Mock(id_table)
    check_columns = Mock()
    create_table = Mock()
    monkeypatch.setattr(csv_module, '_read_table', read_table)
    monkeypatch.setattr(csv_module, '_check_column_names_for_id_table', check_columns)
    monkeypatch.setattr(csv_module, '_create_sqlite_id_table', create_table)
    connection = sqlite3.connect(':memory:')

    _import_id_table('id_region', 'source', connection)

    read_table.assert_called_once_with('id_region', 'source')
    check_columns.assert_called_once_with(id_table)
    create_table.assert_called_once_with('id_region', id_table, connection)
    connection.close()


def test_import_id_tables_calls_import_for_each_table(monkeypatch):
    imported = []
    monkeypatch.setattr(
        csv_module, '_import_id_table', lambda name, source, connection: imported.append((name, source, connection))
    )
    connection = sqlite3.connect(':memory:')

    _import_id_tables(['id_region', 'id_site'], 'source', connection)

    assert imported == [('id_region', 'source', connection), ('id_site', 'source', connection)]
    connection.close()


def test_import_tables_calls_import_for_each_table(monkeypatch):
    imported = []
    monkeypatch.setattr(csv_module, '_import_table', lambda name, source, connection: imported.append((name, source, connection)))
    connection = sqlite3.connect(':memory:')

    _import_tables(['process', 'mapping'], 'source', connection)

    assert imported == [('process', 'source', connection), ('mapping', 'source', connection)]
    connection.close()


def test_check_id_names_for_typos_logs_warning_for_suggestions(monkeypatch):
    monkeypatch.setattr(csv_module.pd, 'read_sql_query', lambda query, connection: pd.DataFrame([{'name': 'erors'}]))
    monkeypatch.setattr(csv_module, 'check', lambda text: {'erors': 'errors'})
    mocked_warning = Mock()
    monkeypatch.setattr(csv_module.logging, 'warning', mocked_warning)

    _check_id_names_for_typos('id_region', sqlite3.connect(':memory:'))

    assert mocked_warning.called
    assert 'potential typo' in mocked_warning.call_args.args[0]


def test_check_id_names_for_typos_skips_clean_values(monkeypatch):
    monkeypatch.setattr(csv_module.pd, 'read_sql_query', lambda query, connection: pd.DataFrame([{'name': 'clean'}]))
    monkeypatch.setattr(csv_module, 'check', lambda text: {})
    mocked_warning = Mock()
    monkeypatch.setattr(csv_module.logging, 'warning', mocked_warning)

    _check_id_names_for_typos('id_region', sqlite3.connect(':memory:'))

    mocked_warning.assert_not_called()


def test_import_table_creates_table_and_inserts_rows(tmp_path):
    connection = sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE id_region(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute('CREATE TABLE id_process(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute("INSERT INTO id_region VALUES (1, 'North')")
    connection.execute("INSERT INTO id_process VALUES (10, 'A')")
    connection.execute("INSERT INTO id_process VALUES (11, 'B')")
    connection.commit()
    table = pd.DataFrame(
        [
            {'id_region': 1, 'id_process': 10, 'value': 3.5},
            {'id_region': 1, 'id_process': 11, 'value': 4.5},
        ]
    )

    with patch(csv_module._read_table, table):
        _import_table('demand', tmp_path, connection)

    rows = connection.execute('SELECT id_region, id_process, value FROM demand ORDER BY id_process').fetchall()
    assert rows == [(1, 10, 3.5), (1, 11, 4.5)]
    connection.close()


def test_import_table_allows_nullable_capture_mechanism_column(tmp_path):
    connection = sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE id_region(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute('CREATE TABLE id_capture_mechanism(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute("INSERT INTO id_region VALUES (1, 'North')")
    connection.execute("INSERT INTO id_capture_mechanism VALUES (2, 'CCS')")
    connection.commit()
    table = pd.DataFrame(
        [
            {'id_region': 1, 'id_capture_mechanism': None, 'value': 3.5},
        ]
    )

    with patch(csv_module._read_table, table):
        _import_table('capture_table', tmp_path, connection)

    rows = connection.execute('SELECT id_region, id_capture_mechanism, value FROM capture_table').fetchall()
    assert rows == [(1, None, 3.5)]
    connection.close()


def test_import_table_logs_schema_on_operational_error(tmp_path, caplog):
    table = pd.DataFrame([{'id_region': 1, 'value': 3.5}])
    connection = type(
        'BrokenConnection',
        (),
        {
            'cursor': lambda self: type(
                'BrokenCursor',
                (),
                {'execute': lambda self, _query: (_ for _ in ()).throw(sqlite3.OperationalError('bad schema'))},
            )()
        },
    )()

    caplog.set_level('ERROR')

    with patch(csv_module._read_table, table), pytest.raises(sqlite3.OperationalError, match='bad schema'):
        _import_table('demand', tmp_path, connection)

    assert "Failed to create table 'demand' with schema" in caplog.text


def test_main_initializes_logging_and_runs_conversion(monkeypatch):
    initialize_logging = Mock()
    convert = Mock()
    monkeypatch.setattr(csv_module.logging_utils, 'initialize_logging', initialize_logging)
    monkeypatch.setattr(csv_module, 'csv_to_sqlite', convert)

    main()

    initialize_logging.assert_called_once_with(log_level=logging.DEBUG)
    convert.assert_called_once_with('../resources/input/por', '../resources/input/por.sqlite')


def test_module_main_guard_executes_main(monkeypatch):
    initialize_logging = Mock()
    monkeypatch.setattr(csv_module.logging_utils, 'initialize_logging', initialize_logging)

    with pytest.raises(FileNotFoundError, match='Source directory not found'):
        runpy.run_path(csv_module.__file__, run_name='__main__')

    initialize_logging.assert_called_once_with(log_level=logging.DEBUG)


def test_create_sqlite_id_table_logs_on_unique_constraint_failure(monkeypatch):
    """Test lines 133-141: logs duplicate ID error message before re-raising IntegrityError."""
    connection = sqlite3.connect(':memory:')
    id_table = pd.DataFrame([{'id': 1, 'name': 'North'}, {'id': 1, 'name': 'South'}])
    mocked_exception_log = Mock()
    monkeypatch.setattr(csv_module.logging, 'exception', mocked_exception_log)

    with pytest.raises(sqlite3.IntegrityError):
        _create_sqlite_id_table('id_region', id_table, connection)

    mocked_exception_log.assert_called_once()
    logged_message = mocked_exception_log.call_args.args[0]
    assert 'duplicate id values' in logged_message
    assert 'id_region' in logged_message
    connection.close()


def test_create_sqlite_id_table_raises_on_non_unique_integrity_error(monkeypatch):
    """Test line 131->139: re-raises IntegrityError that's NOT a UNIQUE constraint error."""
    from unittest.mock import MagicMock

    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value = cursor

    id_table = pd.DataFrame([{'id': 1, 'name': 'North'}])

    # Mock executemany to raise a non-UNIQUE IntegrityError
    cursor.executemany.side_effect = sqlite3.IntegrityError('NOT NULL constraint failed: name')

    # Should re-raise the IntegrityError without special logging
    with pytest.raises(sqlite3.IntegrityError, match='NOT NULL constraint failed'):
        _create_sqlite_id_table('id_region', id_table, connection)


def test_import_table_includes_primary_key_when_id_columns_exist(tmp_path):
    """Test lines 179-181: PRIMARY KEY is added when id_columns exist."""
    connection = sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE id_region(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute('CREATE TABLE id_process(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute("INSERT INTO id_region VALUES (1, 'North')")
    connection.execute("INSERT INTO id_process VALUES (10, 'A')")
    connection.commit()
    table = pd.DataFrame([{'id_region': 1, 'id_process': 10, 'value': 3.5}])

    with patch(csv_module._read_table, table):
        _import_table('demand', tmp_path, connection)

    # Verify PRIMARY KEY constraint exists by enforcing uniqueness
    schema = connection.execute('PRAGMA table_info(demand)').fetchall()
    assert len(schema) == 3
    # Verify PRIMARY KEY constraint prevents duplicate combinations
    with pytest.raises(sqlite3.IntegrityError, match='UNIQUE constraint failed'):
        connection.execute('INSERT INTO demand VALUES (1, 10, 4.5)')
    connection.close()


def test_import_table_includes_foreign_keys_when_id_columns_exist(tmp_path):
    """Test lines 181-183: FOREIGN KEY definitions are added when id_columns match id_ prefix."""
    connection = sqlite3.connect(':memory:')
    connection.execute('PRAGMA foreign_keys = ON')
    connection.execute('CREATE TABLE id_region(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute('CREATE TABLE id_process(id INTEGER PRIMARY KEY, name TEXT)')
    connection.execute("INSERT INTO id_region VALUES (1, 'North')")
    connection.execute("INSERT INTO id_process VALUES (10, 'A')")
    connection.commit()
    table = pd.DataFrame([{'id_region': 1, 'id_process': 10, 'value': 3.5}])

    with patch(csv_module._read_table, table):
        _import_table('demand', tmp_path, connection)

    # Verify FOREIGN KEY constraints exist by checking that invalid references fail
    with pytest.raises(sqlite3.IntegrityError, match='FOREIGN KEY'):
        connection.execute('INSERT INTO demand VALUES (999, 10, 5.5)')
    connection.close()


def test_import_table_no_primary_key_when_no_id_columns(tmp_path):
    """Test that PRIMARY KEY is not added when there are no id columns."""
    connection = sqlite3.connect(':memory:')
    table = pd.DataFrame([{'value': 3.5}, {'value': 4.5}])

    with patch(csv_module._read_table, table):
        _import_table('metrics', tmp_path, connection)

    # Verify table was created without PRIMARY KEY
    rows = connection.execute('SELECT * FROM metrics').fetchall()
    assert len(rows) == 2
    # Should be able to insert duplicate values since no PRIMARY KEY
    connection.execute('INSERT INTO metrics VALUES (3.5)')
    connection.commit()
    connection.close()
