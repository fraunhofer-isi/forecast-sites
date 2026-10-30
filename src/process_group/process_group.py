# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from processes.process import Process


class ProcessGroup:
    """
    Represents a group of processes for visualization purposes.

    Groups processes together to prevent crowding in diagram visualizations.
    Each group has a human-readable name and aggregates energy demands and costs
    for all contained processes.

    Attributes:
        _id: Unique identifier for the process group
        _name: Human-readable name for the group (e.g., "Auxiliary processes", "Conversion units")
        _description: Optional detailed description of the group's purpose
        _processes: List of Process objects in this group

    """

    def __init__(self, id_process_group: int, name: str, description: str = '') -> None:
        """
        Initialize a ProcessGroup.

        Args:
            id_process_group: Unique identifier for this process group
            name: Human-readable name for the group
            description: Optional description of the group's purpose

        """
        self._id = id_process_group
        self._name = name
        self._description = description
        self._processes: list[Process] = []

    @property
    def id(self) -> int:
        """Unique identifier for this process group"""
        return self._id

    @property
    def name(self) -> str:
        """Human-readable name for the group"""
        return self._name

    @property
    def description(self) -> str:
        """Detailed description of the group's purpose"""
        return self._description

    @property
    def processes(self) -> list['Process']:
        """List of Process objects in this group"""
        return self._processes

    def add_process(self, process: 'Process') -> None:
        """
        Add a process to this group.

        Args:
            process: Process object to add to the group

        Raises:
            TypeError: If process is not a Process instance

        """
        if not hasattr(process, 'id'):
            msg = f'Expected Process instance, got {type(process).__name__}'
            raise TypeError(msg)
        self._processes.append(process)

    def process_ids(self) -> list[int]:
        """Get list of IDs for all processes in this group"""
        return [process.id for process in self._processes]

    def __repr__(self) -> str:
        process_count = len(self._processes)
        return f'ProcessGroup({self._id}, {self._name!r}, {process_count} processes)'

    def __len__(self) -> int:
        """Return number of processes in this group"""
        return len(self._processes)

    def __iter__(self):
        """Allow iteration over processes in this group"""
        return iter(self._processes)
