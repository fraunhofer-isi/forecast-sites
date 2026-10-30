# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging
import sqlite3


def create_process_group_tables(connection: sqlite3.Connection) -> bool:
    """
    Create process_group and process_process_group tables if they don't exist.

    This migration adds support for grouping processes for visualization purposes.

    Tables created:
    - process_group: Stores group definitions (name, description)
    - process_process_group: Maps processes to groups

    Args:
        connection: SQLite database connection

    Returns:
        True if tables were created, False if they already exist

    Raises:
        sqlite3.DatabaseError: If table creation fails

    """
    cursor = connection.cursor()

    try:
        # Check if process_group table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='process_group'")
        if cursor.fetchone():
            logging.debug('process_group table already exists')
            return False

        logging.info('Creating process_group and process_process_group tables...')

        # Create process_group table
        cursor.execute("""
            CREATE TABLE "process_group" (
                id_process_group INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            )
            """)
        logging.debug('Created process_group table')

        # Create process_process_group mapping table
        cursor.execute("""
            CREATE TABLE "process_process_group" (
                id_process INTEGER NOT NULL,
                id_process_group INTEGER NOT NULL,
                PRIMARY KEY (id_process, id_process_group),
                FOREIGN KEY (id_process_group) REFERENCES process_group(id_process_group)
            )
            """)
        logging.debug('Created process_process_group table')

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX idx_process_process_group_group
            ON process_process_group(id_process_group)
            """)
        logging.debug('Created index on process_process_group')

        connection.commit()
        logging.info('Process group tables created successfully')
    except sqlite3.DatabaseError:
        logging.exception('Failed to create process_group tables: %s')
        connection.rollback()
        raise
    return True


def get_or_create_default_groups(connection: sqlite3.Connection) -> dict:
    """
    Create default process groups if none exist.

    Default groups:
    - "Ungrouped": Processes not assigned to a specific group
    - "Auxiliary": Support/auxiliary processes
    - "Conversion": Main conversion/transformation processes

    Args:
        connection: SQLite database connection

    Returns:
        Dictionary mapping group name to id_process_group

    """
    cursor = connection.cursor()

    default_groups = {
        'Ungrouped': 'Processes not assigned to a specific group',
        'Auxiliary': 'Support and auxiliary processes',
        'Conversion': 'Main conversion and transformation processes',
    }

    group_ids = {}

    try:
        for group_name, description in default_groups.items():
            # Check if group already exists
            cursor.execute(
                'SELECT id_process_group FROM process_group WHERE name = ?',
                (group_name,),
            )
            result = cursor.fetchone()

            if result:
                group_ids[group_name] = result[0]
            else:
                # Insert new group
                cursor.execute(
                    'INSERT INTO process_group (name, description) VALUES (?, ?)',
                    (group_name, description),
                )
                group_ids[group_name] = cursor.lastrowid

        connection.commit()
        logging.info('Default process groups created: %s', list(group_ids.keys()))
    except sqlite3.DatabaseError:
        logging.exception('Failed to create default process groups: %s')
        connection.rollback()
        raise
    return group_ids


def add_process_to_group(
    connection: sqlite3.Connection,
    id_process: int,
    id_process_group: int,
) -> bool:
    """
    Add a process to a group.

    Args:
        connection: SQLite database connection
        id_process: Process identifier
        id_process_group: Process group identifier

    Returns:
        True if mapping was added, False if it already exists

    Raises:
        sqlite3.DatabaseError: If operation fails

    """
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO process_process_group
            (id_process, id_process_group) VALUES (?, ?)
            """,
            (id_process, id_process_group),
        )
        connection.commit()
    except sqlite3.DatabaseError:
        logging.exception('Failed to add process to group: %s')
        connection.rollback()
        raise
    return cursor.rowcount > 0


def remove_process_from_group(
    connection: sqlite3.Connection,
    id_process: int,
    id_process_group: int,
) -> bool:
    """
    Remove a process from a group.

    Args:
        connection: SQLite database connection
        id_process: Process identifier
        id_process_group: Process group identifier

    Returns:
        True if mapping was removed, False if it didn't exist

    """
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM process_process_group
            WHERE id_process = ? AND id_process_group = ?
            """,
            (id_process, id_process_group),
        )
        connection.commit()
    except sqlite3.DatabaseError:
        logging.exception('Failed to remove process from group: %s')
        connection.rollback()
        raise
    return cursor.rowcount > 0


def get_processes_in_group(
    connection: sqlite3.Connection,
    id_process_group: int,
) -> list:
    """
    Get all process IDs in a group.

    Args:
        connection: SQLite database connection
        id_process_group: Process group identifier

    Returns:
        List of process IDs in the group

    """
    cursor = connection.cursor()

    try:
        cursor.execute(
            'SELECT id_process FROM process_process_group WHERE id_process_group = ?',
            (id_process_group,),
        )
        return [row[0] for row in cursor.fetchall()]

    except sqlite3.DatabaseError:
        logging.exception('Failed to get processes in group: %s')
        raise
