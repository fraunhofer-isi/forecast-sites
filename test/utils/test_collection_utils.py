# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from utils.collection_utils import (
    join_with_comma,
    min_object,
    object_sum,
    unique_list_preserving_order,
)


class TestMinObject:
    """Test the min_object utility function."""

    def test_min_from_collection(self):
        """Should find object with minimum function value."""
        objects = [{'value': 10}, {'value': 5}, {'value': 20}]
        default = {'value': 100}
        result = min_object(objects, lambda x: x['value'], default)
        assert result == {'value': 5}

    def test_uses_default_when_collection_empty(self):
        """Should return default when collection is empty."""
        objects = []
        default = {'value': 100}
        result = min_object(objects, lambda x: x['value'], default)
        assert result == default

    def test_default_is_min(self):
        """Should return default if it has the minimum value."""
        objects = [{'value': 100}, {'value': 200}]
        default = {'value': 50}
        result = min_object(objects, lambda x: x['value'], default)
        assert result == default

    def test_first_min_wins(self):
        """When multiple objects have same min value, first one wins."""
        objects = [{'id': 1, 'value': 10}, {'id': 2, 'value': 10}]
        default = {'id': 0, 'value': 20}
        result = min_object(objects, lambda x: x['value'], default)
        assert result['id'] == 1

    def test_with_numeric_values(self):
        """Should work with numeric objects."""
        objects = [5, 2, 8, 1]
        result = min_object(objects, lambda x: x, 100)
        assert result == 1

    def test_with_complex_function(self):
        """Should work with complex min function."""
        objects = [{'a': 10, 'b': 5}, {'a': 3, 'b': 7}]
        # Find object where a+b is minimum
        result = min_object(objects, lambda x: x['a'] + x['b'], {'a': 100, 'b': 100})
        assert result == {'a': 3, 'b': 7}

    def test_with_single_object(self):
        """Should handle collection with single object."""
        objects = [{'value': 50}]
        result = min_object(objects, lambda x: x['value'], {'value': 100})
        assert result == {'value': 50}


class TestObjectSum:
    """Test the object_sum utility function."""

    def test_basic_sum(self):
        """Should sum values extracted from objects."""
        objects = [{'value': 10}, {'value': 20}, {'value': 30}]
        result = object_sum(objects, lambda x: x['value'])
        assert result == 60

    def test_empty_collection(self):
        """Should return 0 for empty collection."""
        objects = []
        result = object_sum(objects, lambda x: x)
        assert result == 0

    def test_single_object(self):
        """Should handle single object."""
        objects = [{'value': 42}]
        result = object_sum(objects, lambda x: x['value'])
        assert result == 42

    def test_with_numeric_objects(self):
        """Should work with numeric values directly."""
        objects = [1, 2, 3, 4, 5]
        result = object_sum(objects, lambda x: x)
        assert result == 15

    def test_with_complex_extraction(self):
        """Should work with complex value extraction."""
        objects = [{'a': 10, 'b': 5}, {'a': 3, 'b': 7}]
        # Sum (a * b) for each object
        result = object_sum(objects, lambda x: x['a'] * x['b'])
        assert result == 50 + 21

    def test_with_negative_values(self):
        """Should handle negative values."""
        objects = [{'value': 10}, {'value': -5}, {'value': 3}]
        result = object_sum(objects, lambda x: x['value'])
        assert result == 8

    def test_with_float_values(self):
        """Should work with floating point values."""
        objects = [{'value': 10.5}, {'value': 20.3}, {'value': 5.2}]
        result = object_sum(objects, lambda x: x['value'])
        assert result == pytest.approx(36.0)


class TestJoinWithComma:
    """Test the join_with_comma utility function."""

    def test_basic_join(self):
        """Should join items with comma and space."""
        items = [1, 2, 3]
        result = join_with_comma(items)
        assert result == '1, 2, 3'

    def test_string_items(self):
        """Should work with string items."""
        items = ['apple', 'banana', 'cherry']
        result = join_with_comma(items)
        assert result == 'apple, banana, cherry'

    def test_single_item(self):
        """Should handle single item."""
        items = ['only']
        result = join_with_comma(items)
        assert result == 'only'

    def test_empty_collection(self):
        """Should return empty string for empty collection."""
        items = []
        result = join_with_comma(items)
        assert result == ''

    def test_mixed_types(self):
        """Should convert mixed types to strings."""
        items = [1, 'two', 3.0, True]
        result = join_with_comma(items)
        assert result == '1, two, 3.0, True'

    def test_with_objects(self):
        """Should convert objects using their __str__ method."""

        class Item:
            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        items = [Item('first'), Item('second')]
        result = join_with_comma(items)
        assert result == 'first, second'


class TestUniqueListPreservingOrder:
    """Test the unique_list_preserving_order utility function."""

    def test_basic_unique(self):
        """Should return unique items preserving order."""
        items = [1, 2, 1, 3, 2, 4]
        result = unique_list_preserving_order(items)
        assert result == [1, 2, 3, 4]

    def test_already_unique(self):
        """Should return same list if already unique."""
        items = [1, 2, 3, 4]
        result = unique_list_preserving_order(items)
        assert result == [1, 2, 3, 4]

    def test_all_duplicates(self):
        """Should handle list with all duplicates."""
        items = [5, 5, 5, 5]
        result = unique_list_preserving_order(items)
        assert result == [5]

    def test_empty_list(self):
        """Should handle empty list."""
        items = []
        result = unique_list_preserving_order(items)
        assert result == []

    def test_single_item(self):
        """Should handle single item."""
        items = [42]
        result = unique_list_preserving_order(items)
        assert result == [42]

    def test_with_strings(self):
        """Should work with strings."""
        items = ['apple', 'banana', 'apple', 'cherry', 'banana']
        result = unique_list_preserving_order(items)
        assert result == ['apple', 'banana', 'cherry']

    def test_preserves_first_occurrence(self):
        """Should preserve order of first occurrence."""
        items = [3, 1, 2, 1, 3, 2, 4]
        result = unique_list_preserving_order(items)
        assert result == [3, 1, 2, 4]

    def test_with_mixed_types(self):
        """Should work with hashable mixed types."""
        items = [1, '1', 1, '1', 2]
        result = unique_list_preserving_order(items)
        assert result == [1, '1', 2]

    def test_order_preservation_important(self):
        """Verify order is truly preserved (not sorted)."""
        items = [10, 5, 10, 1, 5, 3]
        result = unique_list_preserving_order(items)
        assert result == [10, 5, 1, 3]
        # Verify it's NOT sorted
        assert result != [1, 3, 5, 10]
