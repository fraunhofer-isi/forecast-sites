# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""CLI helper to dump every table in a SQLite DB to CSV files."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

SYSTEM_TABLE_PREFIX = 'sqlite_'
FETCH_BATCH_SIZE = 5000


def main():
    database_file = './resources/input/por_paper_3scenarios.sqlite'
    output_directory = './resources/input/por'

    sqlite_to_csv(database_file, output_directory)


def sqlite_to_csv(database_file: str, output_directory: str):
    _check_if_database_exists(database_file)

    _create_output_directory_if_not_exists(output_directory)

    with sqlite3.connect(database_file) as connection:
        table_names = _fetch_table_names(connection)
        _export_tables_as_csv(
            connection,
            table_names,
            output_directory,
        )


def _create_output_directory_if_not_exists(output_directory: str):
    output_directory_path = Path(output_directory).resolve()
    output_directory_path.mkdir(parents=True, exist_ok=True)


def _check_if_database_exists(database_file):
    database_path = Path(database_file).resolve()
    if not database_path.is_file():
        message = f'SQLite database not found: {database_path}'
        raise FileNotFoundError(message)


def _fetch_table_names(connection):
    query = "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE 'sqlite_%' ORDER BY name"
    rows = connection.execute(query, ('table',)).fetchall()
    table_names = [r[0] for r in rows]
    return table_names


def _export_tables_as_csv(
    connection,
    table_names,
    output_directory,
):
    for table_name in table_names:
        output_path = Path(output_directory) / f'{table_name}.csv'
        if output_path.exists():
            # delete file
            output_path.unlink()

        sql = f'SELECT * FROM "{table_name}"'
        cursor = connection.execute(sql)
        columns = [col[0] for col in cursor.description]
        with output_path.open('w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(columns)
            while True:
                batch = cursor.fetchmany(FETCH_BATCH_SIZE)
                if not batch:
                    break
                writer.writerows(batch)


if __name__ == '__main__':
    main()
