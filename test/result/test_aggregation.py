# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import patch

from result import aggregation
from result.aggregation import aggregate_dictionaries


class TestAggregateDictionaries:
    def test_with_empty_dictionary(self):
        result = aggregate_dictionaries({})
        assert result == {}

    def test_with_empty_sub_dictionaries(self):
        result = aggregate_dictionaries(
            {
                'a': {},
                'b': {},
            }
        )
        assert result == {}

    @patch(aggregation._aggregate_dictionaries_for_key, 'mocked_result')
    def test_normal_usage(self):
        result = aggregate_dictionaries(
            {
                'a': {'x': 1, 'y': 2},
                'b': {'x': 3, 'y': 4},
            }
        )
        assert result == 'mocked_result'


@patch(
    aggregation._aggregate_dictionary_for_key,
    ('mocked_result', 'mocked_aggregated_dictionary'),
)
class TestAggregateDictionariesForKey:
    def test_without_entry(self):
        key = 'x'
        aggregated_results = {}
        dictionary_of_dictionaries = {
            'a': {'x': 1, 'y': 2},
            'b': {'x': 3, 'y': 4},
        }
        result = aggregation._aggregate_dictionaries_for_key(
            key,
            aggregated_results,
            dictionary_of_dictionaries,
        )

        assert result == 'mocked_result'

    def test_with_entry(self):
        key = 'y'
        aggregated_results = {'x': 0, 'y': 0}

        dictionary_of_dictionaries = {
            'a': {'x': 1, 'y': 2},
            'b': {'x': 3, 'y': 4},
        }
        result = aggregation._aggregate_dictionaries_for_key(
            key,
            aggregated_results,
            dictionary_of_dictionaries,
        )

        assert result == 'mocked_result'


class TestAggregateDictionaryForKey:
    def test_with_sub_dictionary(self):
        dictionary = {'x': {'foo': 1, 'baa': 2}, 'y': {'foo': 1, 'baa': 2}}
        key = 'x'
        aggregated_results = {'x': {}}
        aggregated_dictionary = {}
        aggregated_results, aggregated_dictionary = aggregation._aggregate_dictionary_for_key(
            dictionary,
            key,
            aggregated_results,
            aggregated_dictionary,
        )
        assert aggregated_results == {'x': {}}
        assert aggregated_dictionary == {'foo': 1, 'baa': 2}

        aggregated_results, aggregated_dictionary = aggregation._aggregate_dictionary_for_key(
            dictionary,
            key,
            aggregated_results,
            aggregated_dictionary,
        )
        assert aggregated_results == {'x': {}}
        assert aggregated_dictionary == {'foo': 2, 'baa': 4}

    def test_with_value(self):
        dictionary = {
            'x': 5,
            'y': 10,
        }
        key = 'x'
        aggregated_results = {'x': {}}
        aggregated_dictionary = {}
        aggregated_results, aggregated_dictionary = aggregation._aggregate_dictionary_for_key(
            dictionary,
            key,
            aggregated_results,
            aggregated_dictionary,
        )
        assert aggregated_results == {'x': 5}
        assert aggregated_dictionary == {}

    def test_with_value_accumulation(self):
        """Test that scalar values accumulate when encountered multiple times."""
        dictionary = {'x': 5, 'y': 10}
        key = 'x'
        aggregated_results = {'x': {}}
        aggregated_dictionary = {}

        # First call: dict -> scalar transition (line 66 branch)
        aggregated_results, aggregated_dictionary = aggregation._aggregate_dictionary_for_key(
            dictionary,
            key,
            aggregated_results,
            aggregated_dictionary,
        )
        assert aggregated_results == {'x': 5}

        # Second call: scalar -> scalar accumulation
        aggregated_results, aggregated_dictionary = aggregation._aggregate_dictionary_for_key(
            dictionary,
            key,
            aggregated_results,
            aggregated_dictionary,
        )
        assert aggregated_results == {'x': 10}
