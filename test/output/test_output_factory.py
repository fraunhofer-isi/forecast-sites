# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pandas as pd
import pytest

from output.output_factory import OutputFactory


class TestOutputFactory:
    """Test the OutputFactory base class."""

    @pytest.fixture
    def mock_output_data(self):
        """Create mock output data."""
        return pd.DataFrame(
            {
                'id_process': [1, 1, 2, 2],
                'id_product': [10, 11, 10, 12],
                'amount': [100, 50, 200, 30],
            }
        ).set_index('id_process')

    @pytest.fixture
    def mock_carriers(self):
        """Create mock carriers map."""
        return {
            10: Mock(id=10, name='Product A'),
            11: Mock(id=11, name='Product B'),
            12: Mock(id=12, name='Product C'),
        }

    def test_factory_initialization(self, mock_output_data, mock_carriers):
        """Should initialize with output data and carriers."""
        factory = OutputFactory(mock_output_data, mock_carriers)
        assert factory is not None

    def test_create_returns_list(self, mock_output_data, mock_carriers):
        """create() should return a list of outputs."""

        # Create concrete subclass for testing
        class ConcreteOutputFactory(OutputFactory):
            def _output(self, row):
                return {'id': row.name, 'amount': row['amount']}

        factory = ConcreteOutputFactory(mock_output_data, mock_carriers)
        outputs = factory.create(1)

        assert isinstance(outputs, list)

    def test_create_retrieves_correct_process_outputs(self, mock_output_data, mock_carriers):
        """Should return only outputs for specified process."""

        class ConcreteOutputFactory(OutputFactory):
            def _output(self, row):
                return {'id': row.name, 'amount': row['amount']}

        factory = ConcreteOutputFactory(mock_output_data, mock_carriers)
        outputs_p1 = factory.create(1)

        # Process 1 should have 2 outputs
        assert len(outputs_p1) == 2

    def test_create_nonexistent_process(self, mock_output_data, mock_carriers):
        """Should return empty list for nonexistent process (pandas query returns empty DataFrame)."""

        class ConcreteOutputFactory(OutputFactory):
            def _output(self, row):
                return row

        factory = ConcreteOutputFactory(mock_output_data, mock_carriers)

        # Pandas query returns empty DataFrame, not a KeyError
        outputs = factory.create(999)
        assert outputs == []

    def test_output_method_not_implemented(self, mock_output_data, mock_carriers):
        """Base class _output method should raise NotImplementedError."""
        factory = OutputFactory(mock_output_data, mock_carriers)

        with pytest.raises(NotImplementedError, match='Needs to be implemented by inheriting classes'):
            factory.create(1)

    def test_output_entries_for_process_filtering(self, mock_output_data, mock_carriers):
        """_output_entries_for_process should filter by process ID."""
        factory = OutputFactory(mock_output_data, mock_carriers)

        entries_p1 = factory._output_entries_for_process(1)
        assert len(entries_p1) == 2

        entries_p2 = factory._output_entries_for_process(2)
        assert len(entries_p2) == 2

    def test_output_entries_structure(self, mock_output_data, mock_carriers):
        """Output entries should have correct structure."""
        factory = OutputFactory(mock_output_data, mock_carriers)

        entries = factory._output_entries_for_process(1)
        # After reset_index and set_index, id_product should be index
        assert 'id_process' not in entries.columns
        assert 'amount' in entries.columns

    def test_output_entries_for_process_raises_key_error_with_clear_message(self, mock_carriers):
        """Should raise a descriptive error when the query backend fails."""
        mock_output_data = Mock()
        mock_output_data.query.side_effect = KeyError('missing')
        factory = OutputFactory(mock_output_data, mock_carriers)

        with pytest.raises(KeyError, match='No entries id_product 123'):
            factory._output_entries_for_process(123)
