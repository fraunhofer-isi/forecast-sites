# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


def aggregate_dictionaries(dictionary_of_dictionaries):
    if not dictionary_of_dictionaries:
        return {}

    first_dictionary = next(iter(dictionary_of_dictionaries.values()))
    if not first_dictionary:
        return {}

    # We assume that all dictionaries have the same keys
    # Those keys will be the keys of the aggregated result
    keys = list(first_dictionary.keys())

    aggregated_results = {}
    for key in keys:
        aggregated_results = _aggregate_dictionaries_for_key(
            key,
            aggregated_results,
            dictionary_of_dictionaries,
        )

    return aggregated_results


def _aggregate_dictionaries_for_key(
    key,
    aggregated_results,
    dictionary_of_dictionaries,
):
    if key not in aggregated_results:
        aggregated_results[key] = {}
    aggregated_dictionary = aggregated_results[key]

    for dictionary in dictionary_of_dictionaries.values():
        aggregated_results, aggregated_dictionary = _aggregate_dictionary_for_key(
            dictionary,
            key,
            aggregated_results,
            aggregated_dictionary,
        )

    return aggregated_results


def _aggregate_dictionary_for_key(
    dictionary,
    key,
    aggregated_results,
    aggregated_dictionary,
):
    sub_dictionary_or_entry = dictionary.get(key)
    if isinstance(sub_dictionary_or_entry, dict):
        sub_dictionary = sub_dictionary_or_entry
        for sub_key, value in sub_dictionary.items():
            if sub_key not in aggregated_dictionary:
                aggregated_dictionary[sub_key] = 0
            aggregated_dictionary[sub_key] += value
    else:
        entry = sub_dictionary_or_entry
        main_entry = aggregated_results[key]
        if isinstance(main_entry, dict):  # pragma: no cover
            # we replace the default dictionary with a single value zero
            aggregated_results[key] = 0
        aggregated_results[key] += entry

    return aggregated_results, aggregated_dictionary
