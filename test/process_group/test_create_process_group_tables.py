# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import sqlite3
from unittest.mock import Mock

import pytest

from process_group.create_process_group_tables import (
    add_process_to_group,
    create_process_group_tables,
    get_or_create_default_groups,
    get_processes_in_group,
    remove_process_from_group,
)


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database."""
    conn = sqlite3.connect(':memory:')
    yield conn
    conn.close()


@pytest.fixture
def db_with_tables(in_memory_db):
    """Create database with process_group tables."""
    create_process_group_tables(in_memory_db)
    return in_memory_db


class TestCreateProcessGroupTables:
    """Test create_process_group_tables function."""

    def test_creates_tables_on_first_call(self, in_memory_db):
        """Should return True and create tables on first call."""
        result = create_process_group_tables(in_memory_db)
        assert result is True

        # Verify tables exist
        cursor = in_memory_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='process_group'")
        assert cursor.fetchone() is not None

    def test_returns_false_on_second_call(self, db_with_tables):
        """Should return False when tables already exist."""
        result = create_process_group_tables(db_with_tables)
        assert result is False

    def test_creates_process_group_table(self, in_memory_db):
        """Should create process_group table with correct schema."""
        create_process_group_tables(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute('PRAGMA table_info(process_group)')
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert 'id_process_group' in columns
        assert 'name' in columns
        assert 'description' in columns

    def test_creates_mapping_table(self, in_memory_db):
        """Should create process_process_group mapping table."""
        create_process_group_tables(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute('PRAGMA table_info(process_process_group)')
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert 'id_process' in columns
        assert 'id_process_group' in columns

    def test_creates_index(self, in_memory_db):
        """Should create index on process_process_group."""
        create_process_group_tables(in_memory_db)

        cursor = in_memory_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_process_process_group_group'")
        assert cursor.fetchone() is not None

    def test_rolls_back_and_reraises_when_table_creation_fails(self):
        """Should roll back and re-raise database errors."""
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchone.return_value = None
        cursor.execute.side_effect = [None, sqlite3.DatabaseError('boom')]

        with pytest.raises(sqlite3.DatabaseError, match='boom'):
            create_process_group_tables(connection)

        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()


class TestGetOrCreateDefaultGroups:
    """Test get_or_create_default_groups function."""

    def test_creates_three_default_groups(self, db_with_tables):
        """Should create three default groups."""
        groups = get_or_create_default_groups(db_with_tables)

        assert len(groups) == 3
        assert 'Ungrouped' in groups
        assert 'Auxiliary' in groups
        assert 'Conversion' in groups

    def test_returns_group_ids(self, db_with_tables):
        """Should return dict mapping group names to IDs."""
        groups = get_or_create_default_groups(db_with_tables)

        for name, group_id in groups.items():
            assert isinstance(name, str)
            assert isinstance(group_id, int)
            assert group_id > 0

    def test_idempotent(self, db_with_tables):
        """Calling twice should return same group IDs."""
        groups1 = get_or_create_default_groups(db_with_tables)
        groups2 = get_or_create_default_groups(db_with_tables)

        assert groups1 == groups2

    def test_groups_have_descriptions(self, db_with_tables):
        """Default groups should have descriptions in database."""
        get_or_create_default_groups(db_with_tables)

        cursor = db_with_tables.cursor()
        cursor.execute('SELECT name, description FROM process_group ORDER BY name')
        groups = {row[0]: row[1] for row in cursor.fetchall()}

        assert groups['Ungrouped'] is not None
        assert groups['Auxiliary'] is not None
        assert groups['Conversion'] is not None

    def test_rolls_back_and_reraises_when_group_insert_fails(self):
        """Should roll back when inserting default groups fails."""
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchone.return_value = None
        cursor.execute.side_effect = [None, sqlite3.DatabaseError('boom')]

        with pytest.raises(sqlite3.DatabaseError, match='boom'):
            get_or_create_default_groups(connection)

        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()


class TestAddProcessToGroup:
    """Test add_process_to_group function."""

    def test_adds_process_to_group(self, db_with_tables):
        """Should add process to group and return True."""
        groups = get_or_create_default_groups(db_with_tables)
        group_id = groups['Ungrouped']

        result = add_process_to_group(db_with_tables, 1, group_id)
        assert result is True

    def test_duplicate_add_returns_false(self, db_with_tables):
        """Should return False when adding duplicate mapping."""
        groups = get_or_create_default_groups(db_with_tables)
        group_id = groups['Ungrouped']

        add_process_to_group(db_with_tables, 1, group_id)
        result = add_process_to_group(db_with_tables, 1, group_id)

        assert result is False

    def test_same_process_multiple_groups(self, db_with_tables):
        """Should allow same process in multiple groups."""
        groups = get_or_create_default_groups(db_with_tables)

        result1 = add_process_to_group(db_with_tables, 1, groups['Ungrouped'])
        result2 = add_process_to_group(db_with_tables, 1, groups['Conversion'])

        assert result1 is True
        assert result2 is True

    def test_rolls_back_and_reraises_when_insert_fails(self):
        """Should roll back when adding a process to a group fails."""
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.execute.side_effect = sqlite3.DatabaseError('boom')

        with pytest.raises(sqlite3.DatabaseError, match='boom'):
            add_process_to_group(connection, 1, 2)

        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()


class TestRemoveProcessFromGroup:
    """Test remove_process_from_group function."""

    def test_removes_process_from_group(self, db_with_tables):
        """Should remove process from group and return True."""
        groups = get_or_create_default_groups(db_with_tables)
        group_id = groups['Ungrouped']

        add_process_to_group(db_with_tables, 1, group_id)
        result = remove_process_from_group(db_with_tables, 1, group_id)

        assert result is True

    def test_remove_nonexistent_returns_false(self, db_with_tables):
        """Should return False when removing non-existent mapping."""
        groups = get_or_create_default_groups(db_with_tables)

        result = remove_process_from_group(db_with_tables, 999, groups['Ungrouped'])
        assert result is False

    def test_remove_leaves_other_mappings(self, db_with_tables):
        """Should leave other process-group mappings intact."""
        groups = get_or_create_default_groups(db_with_tables)

        add_process_to_group(db_with_tables, 1, groups['Ungrouped'])
        add_process_to_group(db_with_tables, 1, groups['Conversion'])

        remove_process_from_group(db_with_tables, 1, groups['Ungrouped'])

        # Process should still be in Conversion group
        processes = get_processes_in_group(db_with_tables, groups['Conversion'])
        assert 1 in processes

    def test_rolls_back_and_reraises_when_delete_fails(self):
        """Should roll back when removing a process from a group fails."""
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.execute.side_effect = sqlite3.DatabaseError('boom')

        with pytest.raises(sqlite3.DatabaseError, match='boom'):
            remove_process_from_group(connection, 1, 2)

        connection.rollback.assert_called_once_with()
        connection.commit.assert_not_called()


class TestGetProcessesInGroup:
    """Test get_processes_in_group function."""

    def test_returns_empty_list_for_empty_group(self, db_with_tables):
        """Should return empty list for group with no processes."""
        groups = get_or_create_default_groups(db_with_tables)

        processes = get_processes_in_group(db_with_tables, groups['Ungrouped'])
        assert processes == []

    def test_returns_processes_in_group(self, db_with_tables):
        """Should return list of process IDs in group."""
        groups = get_or_create_default_groups(db_with_tables)
        group_id = groups['Conversion']

        add_process_to_group(db_with_tables, 1, group_id)
        add_process_to_group(db_with_tables, 2, group_id)
        add_process_to_group(db_with_tables, 3, group_id)

        processes = get_processes_in_group(db_with_tables, group_id)
        assert set(processes) == {1, 2, 3}

    def test_returns_only_specified_group_processes(self, db_with_tables):
        """Should return only processes in specified group."""
        groups = get_or_create_default_groups(db_with_tables)

        add_process_to_group(db_with_tables, 1, groups['Ungrouped'])
        add_process_to_group(db_with_tables, 2, groups['Conversion'])

        processes_ungrouped = get_processes_in_group(db_with_tables, groups['Ungrouped'])
        processes_conversion = get_processes_in_group(db_with_tables, groups['Conversion'])

        assert processes_ungrouped == [1]
        assert processes_conversion == [2]

    def test_reraises_when_query_fails(self):
        """Should re-raise database errors when fetching processes fails."""
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.execute.side_effect = sqlite3.DatabaseError('boom')

        with pytest.raises(sqlite3.DatabaseError, match='boom'):
            get_processes_in_group(connection, 2)
