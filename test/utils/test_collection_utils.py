# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from utils import collection_utils


class TestMinObject:
    def test_normal_usage(self):
        collection = [(1, 2), (1, -5), (0.5, 0.5)]
        default_object = (1, 2)
        result = collection_utils.min_object(collection, lambda obj: obj[0] + obj[1], default_object)
        assert result == (1, -5)

    def test_empty_collection(self):
        default_object = (1, 2)
        result = collection_utils.min_object([], lambda obj: obj[0] + obj[1], default_object)
        assert result == default_object


def test_object_sum():
    collection = [
        {'foo': 1, 'baa': 2},
        {'foo': 10, 'baa': 20},
    ]
    result = collection_utils.object_sum(collection, lambda obj: obj['baa'])
    assert result == 22


def test_object_subtract():
    collection = [
        {'foo': 1, 'baa': 2},
        {'foo': 10, 'baa': 20},
    ]
    result = collection_utils.object_subtract(collection, lambda obj: obj['baa'])
    assert result == -18


def test_join_with_comma():
    result = collection_utils.join_with_comma(['a', 'b', 'c'])
    assert result == 'a, b, c'
