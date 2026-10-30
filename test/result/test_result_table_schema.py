# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Guards the structural properties of the declarative result table schema.

The schema replaced 188 lines of repeated assignments. That repetition had allowed the same table
to be declared twice with no visible effect, so the uniqueness check below is the regression guard
for that defect class.
"""

from result import result_table_schema
from result.visitor.result_table_kind import ResultTableKind

ALL_SCHEMAS = (
    ('ABSOLUTE_RESULT_TABLES', result_table_schema.ABSOLUTE_RESULT_TABLES),
    ('SPECIFIC_RESULT_TABLES', result_table_schema.SPECIFIC_RESULT_TABLES),
)


class TestResultTableSchema:
    def test_table_names_are_unique_within_each_schema(self):
        """Should declare every table exactly once, which repeated assignments could not guarantee."""
        for schema_name, schema in ALL_SCHEMAS:
            table_names = [table_name for table_name, _ in schema]

            duplicates = {name for name in table_names if table_names.count(name) > 1}
            assert duplicates == set(), f'{schema_name} declares {duplicates} more than once'

    def test_absolute_and_specific_schemas_do_not_overlap(self):
        """Should keep totals and per-process-count values in separate result sets."""
        absolute_names = {name for name, _ in result_table_schema.ABSOLUTE_RESULT_TABLES}
        specific_names = {name for name, _ in result_table_schema.SPECIFIC_RESULT_TABLES}

        assert absolute_names & specific_names == set()

    def test_every_declared_kind_is_a_known_result_table_kind(self):
        """Should only use kinds that TabularVisitor can actually create a table for."""
        for schema_name, schema in ALL_SCHEMAS:
            for table_name, table_kind in schema:
                assert isinstance(table_kind, ResultTableKind), f'{schema_name}: {table_name} uses {table_kind!r}'
