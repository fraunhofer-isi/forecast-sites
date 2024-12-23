# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

def min_object(collection, min_function, default_object):
    """
    Loops over the collection and returns the default_object or
    an object of the collection, for which min_function yields
    the minimum value. If several objects provide the same min,
    the first min object wins.
    """

    found_object = default_object
    found_min_value = min_function(default_object)

    for current_object in collection:
        current_min_value = min_function(current_object)
        if current_min_value < found_min_value:
            found_object = current_object
            found_min_value = current_min_value

    return found_object


def object_sum(collection, value_function):
    """
    Loops over the collection and returns the sum of the values returned
    by the value_function (that is called for each object in the collection)
    """
    result = 0
    for current_object in collection:
        result += value_function(current_object)
    return result


def object_subtract(collection, value_function):
    """
    Loops over the collection and returns the sum of the values returned
    by the value_function (that is called for each object in the collection)
    """
    result = 0
    for current_object in collection:
        result -= value_function(current_object)
    return result


def join_with_comma(collection):
    return ', '.join(list(map(str, collection)))
