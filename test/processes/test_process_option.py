# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

from processes.process_option import ProcessOption


class TestProcessOption:
    """Test cases for ProcessOption wrapper."""

    def test_process_option_stores_process(self):
        """Test that ProcessOption stores the process correctly."""
        mock_process = Mock()
        option = ProcessOption(mock_process)
        assert option.process == mock_process

    def test_process_option_repr_includes_process(self):
        """Test that repr includes process information."""
        mock_process = Mock()
        mock_process.__repr__ = Mock(return_value='MockProcess()')
        option = ProcessOption(mock_process)
        repr_str = repr(option)
        assert 'ProcessOption' in repr_str
        assert 'process' in repr_str

    def test_process_option_with_different_processes(self):
        """Test ProcessOption with different process objects."""
        mock_process_1 = Mock(name='process1')
        mock_process_2 = Mock(name='process2')

        option1 = ProcessOption(mock_process_1)
        option2 = ProcessOption(mock_process_2)

        assert option1.process == mock_process_1
        assert option2.process == mock_process_2
        assert option1.process != option2.process

    def test_process_option_stores_reference_not_copy(self):
        """Test that ProcessOption stores a reference to the process."""
        mock_process = Mock()
        option = ProcessOption(mock_process)

        # Modify the mock object
        mock_process.test_attr = 'value'

        # Verify the stored reference reflects the change
        assert option.process.test_attr == 'value'

    def test_process_option_repr_format(self):
        """Test that repr has expected format."""
        mock_process = Mock()
        mock_process.__repr__ = Mock(return_value='Process(id=1)')
        option = ProcessOption(mock_process)
        repr_str = repr(option)
        assert repr_str.startswith('ProcessOption(')
        assert repr_str.endswith(')')
