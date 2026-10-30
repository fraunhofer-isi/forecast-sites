# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


import pandas as pd

from .process_group import ProcessGroup


class ProcessGroupFactory:
    """
    Factory for creating ProcessGroup objects from data sources.

    Handles loading process group definitions from database and linking them
    with actual Process objects from the simulation.
    """

    @staticmethod
    def create_from_dataframe(process_groups_df: pd.DataFrame) -> dict[int, ProcessGroup]:
        """
        Create ProcessGroup objects from a pandas DataFrame.

        Expected DataFrame columns:
        - id_process_group: Unique identifier
        - name: Group name
        - description: Optional group description

        Args:
            process_groups_df: DataFrame containing process group definitions

        Returns:
            Dictionary mapping id_process_group to ProcessGroup objects

        Raises:
            ValueError: If required columns are missing

        """
        required_columns = {'id_process_group', 'name'}
        if not required_columns.issubset(process_groups_df.columns):
            missing = required_columns - set(process_groups_df.columns)
            msg = f'Missing required columns: {missing}'
            raise ValueError(msg)

        process_groups = {}
        for _, row in process_groups_df.iterrows():
            group_id = int(row['id_process_group'])
            name = str(row['name'])
            description = str(row.get('description', ''))

            process_groups[group_id] = ProcessGroup(
                id_process_group=group_id,
                name=name,
                description=description,
            )

        return process_groups

    @staticmethod
    def create_mapping_from_dataframe(
        process_process_group_df: pd.DataFrame,
        process_groups: dict[int, ProcessGroup],
    ) -> dict[int, ProcessGroup]:
        """
        Link processes to their groups using a mapping DataFrame.

        Expected DataFrame columns:
        - id_process: Process identifier
        - id_process_group: Group identifier

        Args:
            process_process_group_df: DataFrame mapping processes to groups
            process_groups: Dictionary of ProcessGroup objects

        Returns:
            Updated dictionary of ProcessGroup objects with processes assigned

        Raises:
            ValueError: If required columns are missing
            KeyError: If referenced process group doesn't exist

        """
        required_columns = {'id_process', 'id_process_group'}
        if not required_columns.issubset(process_process_group_df.columns):
            missing = required_columns - set(process_process_group_df.columns)
            msg = f'Missing required columns: {missing}'
            raise ValueError(msg)

        for _, row in process_process_group_df.iterrows():
            group_id = int(row['id_process_group'])
            process_id = int(row['id_process'])

            if group_id not in process_groups:
                msg = f'Process group {group_id} not found'
                raise KeyError(msg)

            # Note: Process object will be linked separately by caller
            # This mapping just tracks which processes belong to which groups
            if not hasattr(process_groups[group_id], '_process_ids'):
                process_groups[group_id]._process_ids = []
            process_groups[group_id]._process_ids.append(process_id)

        return process_groups

    @staticmethod
    def load_from_database(
        connection, _id_scenario: int, _id_region: int
    ) -> tuple[dict[int, ProcessGroup], dict[int, list[int]]]:
        """
        Load process groups and mappings from database.

        Args:
            connection: SQLite database connection
            id_scenario: Scenario ID filter
            id_region: Region ID filter

        Returns:
            Tuple of (process_groups dict, process_to_group mapping dict)

        Raises:
            FileNotFoundError: If required tables don't exist

        """
        # Load process_group table
        try:
            process_groups_df = pd.read_sql(
                'SELECT * FROM process_group',
                connection,
            )
        except Exception as e:
            msg = 'process_group table not found in database'
            raise FileNotFoundError(msg) from e

        process_groups = ProcessGroupFactory.create_from_dataframe(process_groups_df)

        # Load process_process_group mapping table
        try:
            mapping_df = pd.read_sql(
                'SELECT * FROM process_process_group',
                connection,
            )
        except Exception as e:
            msg = 'process_process_group table not found in database'
            raise FileNotFoundError(msg) from e

        ProcessGroupFactory.create_mapping_from_dataframe(mapping_df, process_groups)

        # Create reverse mapping: process_id -> group_id
        process_to_group = {}
        for group_id, group in process_groups.items():
            if hasattr(group, '_process_ids'):
                for process_id in group._process_ids:
                    process_to_group[process_id] = group_id

        return process_groups, process_to_group
