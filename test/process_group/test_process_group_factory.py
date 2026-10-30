# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pandas as pd
import pytest

from process_group.process_group import ProcessGroup
from process_group.process_group_factory import ProcessGroupFactory


@pytest.fixture
def sample_process_groups_df():
    """Create sample process groups DataFrame."""
    return pd.DataFrame(
        {
            'id_process_group': [1, 2, 3],
            'name': ['Group A', 'Group B', 'Group C'],
            'description': ['First group', 'Second group', 'Third group'],
        }
    )


@pytest.fixture
def sample_mapping_df():
    """Create sample process-to-group mapping DataFrame."""
    return pd.DataFrame({'id_process': [10, 11, 12, 13, 14], 'id_process_group': [1, 1, 2, 2, 3]})


class TestCreateFromDataFrame:
    def test_create_from_dataframe(self, sample_process_groups_df):
        """Should create ProcessGroup objects from DataFrame."""
        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)

        assert len(groups) == 3
        assert isinstance(groups[1], ProcessGroup)
        assert isinstance(groups[2], ProcessGroup)
        assert isinstance(groups[3], ProcessGroup)

    def test_process_group_names(self, sample_process_groups_df):
        """Created groups should have correct names."""
        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)

        assert groups[1].name == 'Group A'
        assert groups[2].name == 'Group B'
        assert groups[3].name == 'Group C'

    def test_process_group_descriptions(self, sample_process_groups_df):
        """Created groups should have correct descriptions."""
        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)

        assert groups[1].description == 'First group'
        assert groups[2].description == 'Second group'
        assert groups[3].description == 'Third group'

    def test_create_from_dataframe_missing_name_column(self):
        """Should raise ValueError if 'name' column is missing."""
        df = pd.DataFrame({'id_process_group': [1, 2], 'description': ['A', 'B']})

        with pytest.raises(ValueError, match='Missing required columns'):
            ProcessGroupFactory.create_from_dataframe(df)

    def test_create_from_dataframe_missing_id_column(self):
        """Should raise ValueError if 'id_process_group' column is missing."""
        df = pd.DataFrame({'name': ['Group A', 'Group B'], 'description': ['A', 'B']})

        with pytest.raises(ValueError, match='Missing required columns'):
            ProcessGroupFactory.create_from_dataframe(df)

    def test_create_from_empty_dataframe(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame({'id_process_group': [], 'name': [], 'description': []})

        groups = ProcessGroupFactory.create_from_dataframe(df)
        assert len(groups) == 0

    def test_create_from_dataframe_uses_empty_description_when_missing(self):
        df = pd.DataFrame(
            {
                'id_process_group': [1],
                'name': ['Group A'],
            }
        )

        groups = ProcessGroupFactory.create_from_dataframe(df)

        assert groups[1].description == ''


class TestCreateMappingFromDataFrame:
    def test_create_mapping_from_dataframe(self, sample_process_groups_df, sample_mapping_df):
        """Should link processes to groups using mapping DataFrame."""
        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)
        updated_groups = ProcessGroupFactory.create_mapping_from_dataframe(sample_mapping_df, groups)

        assert hasattr(updated_groups[1], '_process_ids')
        assert hasattr(updated_groups[2], '_process_ids')
        assert hasattr(updated_groups[3], '_process_ids')

    def test_mapping_process_assignment(self, sample_process_groups_df, sample_mapping_df):
        """Should correctly assign processes to groups."""
        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)
        updated_groups = ProcessGroupFactory.create_mapping_from_dataframe(sample_mapping_df, groups)

        assert updated_groups[1]._process_ids == [10, 11]
        assert updated_groups[2]._process_ids == [12, 13]
        assert updated_groups[3]._process_ids == [14]

    def test_create_mapping_missing_id_process_column(self, sample_process_groups_df):
        """Should raise ValueError if 'id_process' column is missing."""
        df = pd.DataFrame({'id_process_group': [1, 2]})

        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)

        with pytest.raises(ValueError, match='Missing required columns'):
            ProcessGroupFactory.create_mapping_from_dataframe(df, groups)

    def test_create_mapping_missing_group(self, sample_process_groups_df):
        """Should raise KeyError if referenced group doesn't exist."""
        df = pd.DataFrame(
            {
                'id_process': [10, 11],
                'id_process_group': [1, 999],  # 999 doesn't exist
            }
        )

        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)

        with pytest.raises(KeyError, match='Process group 999 not found'):
            ProcessGroupFactory.create_mapping_from_dataframe(df, groups)

    def test_create_mapping_empty_dataframe(self, sample_process_groups_df):
        """Should handle empty mapping DataFrame."""
        df = pd.DataFrame({'id_process': [], 'id_process_group': []})

        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)
        updated_groups = ProcessGroupFactory.create_mapping_from_dataframe(df, groups)

        # Groups should exist but have no processes
        assert 1 in updated_groups
        assert 2 in updated_groups

    def test_create_mapping_appends_to_existing_process_ids(self, sample_process_groups_df):
        groups = ProcessGroupFactory.create_from_dataframe(sample_process_groups_df)
        groups[1]._process_ids = [5]
        mapping_df = pd.DataFrame(
            {
                'id_process': [10, 11],
                'id_process_group': [1, 1],
            }
        )

        updated_groups = ProcessGroupFactory.create_mapping_from_dataframe(mapping_df, groups)

        assert updated_groups[1]._process_ids == [5, 10, 11]


class TestLoadFromDatabase:
    def test_load_from_database_reads_groups_and_builds_reverse_mapping(self):
        connection = Mock()
        process_groups_df = pd.DataFrame(
            {
                'id_process_group': [1, 2],
                'name': ['Group A', 'Group B'],
                'description': ['Desc A', 'Desc B'],
            }
        )
        mapping_df = pd.DataFrame(
            {
                'id_process': [10, 11, 20],
                'id_process_group': [1, 1, 2],
            }
        )
        original_read_sql = pd.read_sql
        pd.read_sql = Mock(side_effect=[process_groups_df, mapping_df])

        try:
            process_groups, process_to_group = ProcessGroupFactory.load_from_database(connection, 1, 2)
        finally:
            pd.read_sql = original_read_sql

        assert set(process_groups) == {1, 2}
        assert process_groups[1]._process_ids == [10, 11]
        assert process_groups[2]._process_ids == [20]
        assert process_to_group == {10: 1, 11: 1, 20: 2}

    def test_load_from_database_with_unmapped_groups(self):
        """Should handle groups that have no processes in the mapping."""
        connection = Mock()
        process_groups_df = pd.DataFrame(
            {
                'id_process_group': [1, 2, 3],
                'name': ['Group A', 'Group B', 'Group C'],
                'description': ['Desc A', 'Desc B', 'Desc C'],
            }
        )
        # Only groups 1 and 2 have processes; group 3 is unmapped
        mapping_df = pd.DataFrame(
            {
                'id_process': [10, 11, 20],
                'id_process_group': [1, 1, 2],
            }
        )
        original_read_sql = pd.read_sql
        pd.read_sql = Mock(side_effect=[process_groups_df, mapping_df])

        try:
            process_groups, process_to_group = ProcessGroupFactory.load_from_database(connection, 1, 2)
        finally:
            pd.read_sql = original_read_sql

        assert set(process_groups) == {1, 2, 3}
        assert process_groups[1]._process_ids == [10, 11]
        assert process_groups[2]._process_ids == [20]
        assert not hasattr(process_groups[3], '_process_ids')  # Unmapped group
        assert process_to_group == {10: 1, 11: 1, 20: 2}

    def test_load_from_database_raises_when_group_table_missing(self):
        connection = Mock()
        original_read_sql = pd.read_sql
        pd.read_sql = Mock(side_effect=Exception('missing table'))

        try:
            with pytest.raises(FileNotFoundError, match='process_group table not found in database'):
                ProcessGroupFactory.load_from_database(connection, 1, 2)
        finally:
            pd.read_sql = original_read_sql

    def test_load_from_database_raises_when_mapping_table_missing(self):
        connection = Mock()
        process_groups_df = pd.DataFrame(
            {
                'id_process_group': [1],
                'name': ['Group A'],
                'description': ['Desc A'],
            }
        )
        original_read_sql = pd.read_sql
        pd.read_sql = Mock(side_effect=[process_groups_df, Exception('missing mapping')])

        try:
            with pytest.raises(FileNotFoundError, match='process_process_group table not found in database'):
                ProcessGroupFactory.load_from_database(connection, 1, 2)
        finally:
            pd.read_sql = original_read_sql
