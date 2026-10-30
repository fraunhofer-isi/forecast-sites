# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from utils import logging_utils
from utils.spell_checker import check


def main():
    csv_source_directory = '../resources/input/por'
    sqlite_database_path = '../resources/input/por.sqlite'
    logging_utils.initialize_logging(log_level=logging.DEBUG)

    csv_to_sqlite(csv_source_directory, sqlite_database_path)


def csv_to_sqlite(csv_source_directory, sqlite_database_path):
    _check_if_directory_exists(csv_source_directory)
    _delete_database_if_exists(sqlite_database_path)

    file_names = _read_csv_file_names_from_directory_without_ending(csv_source_directory)
    id_table_names = _id_table_names(file_names)
    remaining_table_names = _remaining_table_names(file_names, id_table_names)

    connection = sqlite3.connect(sqlite_database_path)
    try:
        logging.debug('Importing id tables...')
        _import_id_tables(id_table_names, csv_source_directory, connection)

        logging.debug('Importing remaining tables...')
        _import_tables(remaining_table_names, csv_source_directory, connection)
    finally:
        connection.close()


def _check_if_directory_exists(source_directory):
    if not Path(source_directory).is_dir():
        message = f'Source directory not found: {source_directory}'
        raise FileNotFoundError(message)


def _delete_database_if_exists(database_path):
    path = Path(database_path).resolve()
    if not path.exists():
        return
    if not path.is_file():
        message = f'Expected a database file at {path}, but found a directory.'
        raise IsADirectoryError(message)
    try:
        path.unlink()
    except PermissionError as exc:
        message = f'Could not delete existing database at {path}: {exc}'
        raise PermissionError(message) from exc


def _read_csv_file_names_from_directory_without_ending(source_directory):
    source_path = Path(source_directory).resolve()
    file_names = [f.name.replace('.csv', '') for f in source_path.glob('*.csv')]
    return file_names


def _id_table_names(file_names):
    id_table_names = [file_name for file_name in file_names if file_name.lower().startswith('id_')]
    return id_table_names


def _remaining_table_names(file_names, id_table_names):
    remaining_table_names = [file_name for file_name in file_names if file_name not in id_table_names]
    return remaining_table_names


def _import_id_tables(id_table_names, source_directory, connection):
    for id_table_name in id_table_names:
        _import_id_table(id_table_name, source_directory, connection)


def _import_tables(table_names, source_directory, connection):
    for table_name in table_names:
        _import_table(table_name, source_directory, connection)


def _read_table(table_name, source_directory):
    file_path = Path(source_directory).resolve() / f'{table_name}.csv'
    df = pd.read_csv(file_path, encoding='latin-1')
    return df


def _import_id_table(id_table_name, source_directory, connection):
    id_table = _read_table(id_table_name, source_directory)
    _check_column_names_for_id_table(id_table)
    _create_sqlite_id_table(id_table_name, id_table, connection)


def _check_column_names_for_id_table(id_table):
    col_names = list(id_table.columns)
    if col_names != ['id', 'name']:
        message = f"Table '{id_table}' must have columns 'id' and 'name' columns, found: {col_names}"
        raise ValueError(message)


def _check_id_names_for_typos(id_table_name, connection):
    df = pd.read_sql_query(f'SELECT * FROM "{id_table_name}"', connection)
    name_series = df['name']

    for name in name_series:
        suggestions = check(name)
        if suggestions:
            message = f"ID table '{id_table_name}' uses a name with a potential typo: '{name}'."
            for word, suggestion in suggestions.items():
                message += f"\nDid you mean '{suggestion}' instead of '{word}'?"
            logging.warning(message)


def _create_sqlite_id_table(id_table_name, id_table, connection):
    cursor = connection.cursor()
    cursor.execute(f"""CREATE TABLE "{id_table_name}" (
        id INTEGER NOT NULL PRIMARY KEY,
        name TEXT NOT NULL
        )""")

    rows = list(id_table[['id', 'name']].itertuples(index=False, name=None))

    try:
        cursor.executemany(f'INSERT INTO "{id_table_name}" (id, name) VALUES (?, ?)', rows)
    except sqlite3.IntegrityError as error:
        error_message = str(error)
        if 'UNIQUE constraint failed' in error_message:
            duplicate_ids = _duplicate_ids(rows)
            message = (
                f"Error: Table '{id_table_name}(_old)' has duplicate id values: {duplicate_ids}. "
                'IDs in original id tables must be unique.'
            )
            logging.exception(message)

        raise

    connection.commit()


def _duplicate_ids(rows):
    id_counts = {}
    for row in rows:
        id_value = row[0]
        if id_value in id_counts:
            id_counts[id_value] += 1
        else:
            id_counts[id_value] = 1
    duplicate_ids = [id_value for id_value, count in id_counts.items() if count > 1]
    return duplicate_ids


def _import_table(table_name, source_directory, connection):
    table = _read_table(table_name, source_directory)

    logger = logging.getLogger(__name__)
    logger.debug("Creating new table '%s' ...", table_name)
    id_columns, value_columns = _identify_columns(table)

    cursor = connection.cursor()
    id_columns_allowing_null_values = ['id_capture_mechanism']
    column_definitions = []
    for id_column in id_columns:
        if id_column in id_columns_allowing_null_values:
            column_definitions.append(f'"{id_column}" INTEGER')
        else:
            column_definitions.append(f'"{id_column}" INTEGER NOT NULL')

    column_definitions += [f'"{col}" REAL' for col in value_columns]
    primary_key_definition = f'PRIMARY KEY ({", ".join([f'"{col}"' for col in id_columns])})' if id_columns else None
    foreign_key_definitions = _foreign_key_definitions(id_columns)

    schema_lines = [', '.join(column_definitions)]
    if primary_key_definition:
        schema_lines.append(primary_key_definition)
    if foreign_key_definitions:
        schema_lines.extend(foreign_key_definitions)
    schema_query = f"""CREATE TABLE "{table_name}" (
        {', '.join(schema_lines)}
    )"""

    try:
        cursor.execute(schema_query)
    except sqlite3.OperationalError:
        logger.exception("Failed to create table '%s' with schema: %s", table_name, schema_query)
        raise

    logger.debug("Inserting data into new table '%s'...", table_name)
    placeholders = ','.join(['?'] * (len(id_columns) + len(value_columns)))
    rows = list(table.itertuples(index=False, name=None))
    cursor.executemany(f'INSERT INTO "{table_name}" VALUES ({placeholders})', rows)

    connection.commit()


def _foreign_key_definitions(id_columns):
    return [
        f'FOREIGN KEY("{col}") REFERENCES id_{col[3:]}(id) ON DELETE CASCADE ON UPDATE CASCADE'
        for col in id_columns
        if col.startswith('id_')
    ]


def _identify_columns(df):
    columns = list(df.columns)
    id_columns = [col for col in columns if col.startswith('id_')]
    value_columns = [col for col in columns if not col.startswith('id_')]
    return id_columns, value_columns


if __name__ == '__main__':
    main()
