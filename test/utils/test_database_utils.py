# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from utils import database_utils


class TestInitializeOutputDatabase:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        # Cleanup
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def input_database(self, temp_dir):
        """Create a temporary input database with sample data."""
        input_db_path = temp_dir / 'input.sqlite'
        connection = sqlite3.connect(input_db_path)
        cursor = connection.cursor()

        # Create sample input table
        cursor.execute('CREATE TABLE test_input_table (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute("INSERT INTO test_input_table VALUES (1, 'test_data')")
        cursor.execute("INSERT INTO test_input_table VALUES (2, 'more_data')")

        connection.commit()
        connection.close()

        return input_db_path

    @pytest.fixture
    def simulation_options(self, input_database, temp_dir):
        """Create simulation options dictionary."""
        return {
            'database_path': str(input_database),
            'output_directory': str(temp_dir / 'output'),
        }

    def test_creates_output_directory_if_missing(self, simulation_options):
        """Test that output directory is created if it doesn't exist."""
        output_dir = Path(simulation_options['output_directory'])

        assert not output_dir.exists()

        database_utils.initialize_output_database(simulation_options)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_copies_input_database_to_output(self, simulation_options):
        """Test that input database is copied to output location."""
        output_db_path = Path(simulation_options['output_directory']) / 'output.sqlite'

        assert not output_db_path.exists()

        database_utils.initialize_output_database(simulation_options)

        assert output_db_path.exists()
        assert output_db_path.is_file()

    def test_preserves_input_tables_in_output(self, simulation_options):
        """Test that input tables are preserved in the output database."""
        database_utils.initialize_output_database(simulation_options)

        output_db_path = Path(simulation_options['output_directory']) / 'output.sqlite'
        connection = sqlite3.connect(output_db_path)
        cursor = connection.cursor()

        # Check that input table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_input_table'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'test_input_table'

        # Check that input data is preserved
        cursor.execute('SELECT id, name FROM test_input_table ORDER BY id')
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0] == (1, 'test_data')
        assert rows[1] == (2, 'more_data')

        connection.close()

    def test_deletes_existing_output_database(self, simulation_options):
        """Test that existing output.sqlite is deleted before copying."""
        output_dir = Path(simulation_options['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        output_db_path = output_dir / 'output.sqlite'

        # Create existing output database with different content
        connection = sqlite3.connect(output_db_path)
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE old_table (id INTEGER PRIMARY KEY)')
        cursor.execute('INSERT INTO old_table VALUES (999)')
        connection.commit()
        connection.close()

        assert output_db_path.exists()

        # Initialize - should delete old database and copy new one
        database_utils.initialize_output_database(simulation_options)

        # Check that old table is gone and new table exists
        connection = sqlite3.connect(output_db_path)
        cursor = connection.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='old_table'")
        assert cursor.fetchone() is None

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_input_table'")
        assert cursor.fetchone() is not None

        connection.close()

    def test_raises_error_if_input_database_not_found(self, temp_dir):
        """Test that FileNotFoundError is raised if input database doesn't exist."""
        simulation_options = {
            'database_path': str(temp_dir / 'nonexistent.sqlite'),
            'output_directory': str(temp_dir / 'output'),
        }

        with pytest.raises(FileNotFoundError, match='Input database not found'):
            database_utils.initialize_output_database(simulation_options)

    def test_creates_nested_output_directories(self, input_database, temp_dir):
        """Test that nested output directories are created."""
        simulation_options = {
            'database_path': str(input_database),
            'output_directory': str(temp_dir / 'level1' / 'level2' / 'output'),
        }

        output_dir = Path(simulation_options['output_directory'])
        assert not output_dir.exists()

        database_utils.initialize_output_database(simulation_options)

        assert output_dir.exists()
        assert (output_dir / 'output.sqlite').exists()

    def test_works_when_output_directory_already_exists(self, simulation_options):
        """Test that initialization works when output directory already exists."""
        output_dir = Path(simulation_options['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)

        assert output_dir.exists()

        database_utils.initialize_output_database(simulation_options)

        assert (output_dir / 'output.sqlite').exists()

    def test_handles_pathlib_paths(self, input_database, temp_dir):
        """Test that function works with Path objects as well as strings."""
        simulation_options = {
            'database_path': input_database,  # Path object
            'output_directory': temp_dir / 'output',  # Path object
        }

        database_utils.initialize_output_database(simulation_options)

        output_db_path = Path(simulation_options['output_directory']) / 'output.sqlite'
        assert output_db_path.exists()
