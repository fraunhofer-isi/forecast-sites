# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging


class ResultTableWriter:
    """Manages tabular result storage and provides entry operations."""

    def __init__(self):
        self.absolute_results = {}
        self.specific_results = {}

    @staticmethod
    def add_entry_at(df, keys, year, value):
        """Add an entry to a result table at the specified keys and year."""
        year_column_name = 'Y' + str(year)
        if year_column_name not in df.columns:
            default_values = [None] * len(df)
            df[year_column_name] = default_values

        if keys not in df.index:
            df.loc[keys, year_column_name] = value
            return

        existing_value = df.loc[keys, year_column_name]
        if existing_value is not None:
            id_column_names = df.index.names
            id_entries = ''
            for id_column_name in id_column_names:
                id_entry = f'{id_column_name}: {keys[id_column_names.index(id_column_name)]}| '
                id_entries += id_entry
            logging.error('Existing id entries:\n%s', id_entries)
            message = (
                f'Entry for keys {keys} and year {year} already exists. '
                f'Value to write: {value}; existing value: {existing_value}.'
            )
            raise KeyError(message)

        df.loc[keys, year_column_name] = value

    @staticmethod
    def add_or_accumulate_entry_at(df, keys, year, value):
        """Add or accumulate an entry in a result table at the specified keys and year."""
        year_column_name = 'Y' + str(year)
        if year_column_name not in df.columns:
            default_values = [None] * len(df)
            df[year_column_name] = default_values

        if keys not in df.index:
            df.loc[keys, year_column_name] = value
            return

        existing_value = df.loc[keys, year_column_name]
        if existing_value is None:
            df.loc[keys, year_column_name] = value
            return

        df.loc[keys, year_column_name] = existing_value + value
