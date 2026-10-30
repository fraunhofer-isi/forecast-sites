# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from process_group.process_group import ProcessGroup


class MockProcess:
    """Mock Process for testing without full dependencies."""

    def __init__(self, id_process: int):
        self.id = id_process


class TestProcessGroup:
    """Tests for ProcessGroup domain class."""

    def test_init_creates_group_with_name(self):
        """ProcessGroup initializes with name and description."""
        group = ProcessGroup(id_process_group=1, name='Auxiliary processes', description='Helper processes')

        assert group.id == 1
        assert group.name == 'Auxiliary processes'
        assert group.description == 'Helper processes'

    def test_init_with_empty_description(self):
        """ProcessGroup allows empty description."""
        group = ProcessGroup(id_process_group=2, name='Conversion units')

        assert group.id == 2
        assert group.name == 'Conversion units'
        assert group.description == ''

    def test_add_process_appends_to_list(self):
        """add_process adds a process to the group."""
        group = ProcessGroup(1, 'Test group')
        process = MockProcess(10)

        group.add_process(process)

        assert len(group.processes) == 1
        assert group.processes[0] is process

    def test_add_multiple_processes(self):
        """Can add multiple processes to a group."""
        group = ProcessGroup(1, 'Test group')
        process1 = MockProcess(10)
        process2 = MockProcess(20)

        group.add_process(process1)
        group.add_process(process2)

        assert len(group.processes) == 2
        assert group.process_ids() == [10, 20]

    def test_add_process_with_invalid_type_raises(self):
        """add_process raises TypeError for non-Process objects."""
        group = ProcessGroup(1, 'Test group')

        with pytest.raises(TypeError):
            group.add_process('not a process')

    def test_process_ids_returns_list(self):
        """process_ids returns list of IDs for all processes."""
        group = ProcessGroup(1, 'Test group')
        group.add_process(MockProcess(10))
        group.add_process(MockProcess(20))
        group.add_process(MockProcess(30))

        assert group.process_ids() == [10, 20, 30]

    def test_process_ids_empty_group(self):
        """process_ids returns empty list for new group."""
        group = ProcessGroup(1, 'Test group')

        assert group.process_ids() == []

    def test_len_returns_process_count(self):
        """__len__ returns count of processes in group."""
        group = ProcessGroup(1, 'Test group')
        assert len(group) == 0

        group.add_process(MockProcess(10))
        assert len(group) == 1

        group.add_process(MockProcess(20))
        assert len(group) == 2

    def test_repr_shows_group_info(self):
        """__repr__ displays group ID, name, and process count."""
        group = ProcessGroup(1, 'Test group')
        group.add_process(MockProcess(10))

        result = repr(group)

        assert 'ProcessGroup' in result
        assert '1' in result
        assert 'Test group' in result
        assert '1 processes' in result

    def test_iter_allows_iteration_over_processes(self):
        """__iter__ allows for-loop over processes."""
        group = ProcessGroup(1, 'Test group')
        process1 = MockProcess(10)
        process2 = MockProcess(20)
        group.add_process(process1)
        group.add_process(process2)

        collected = list(group)

        assert collected == [process1, process2]

    def test_properties_are_read_only(self):
        """Properties return correct values and are access-controlled."""
        group = ProcessGroup(1, 'Test group', 'Test description')

        assert group.id == 1
        assert group.name == 'Test group'
        assert group.description == 'Test description'
        assert isinstance(group.processes, list)
