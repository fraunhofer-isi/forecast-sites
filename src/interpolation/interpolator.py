# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging


def interpolate(
    year,
    simulation_options,
    interpolation_data,
):
    start_year = simulation_options['start_year']
    end_year = simulation_options['end_year']
    interim_year = simulation_options['interim_year']

    value_for_start_year = interpolation_data.value_for_start_year
    value_for_interim_year = interpolation_data.value_for_interim_year
    value_for_end_year = interpolation_data.value_for_end_year

    if value_for_interim_year is None:
        slope = (value_for_end_year - value_for_start_year) / (end_year - start_year)
        value = value_for_start_year + slope * (year - start_year)
    elif year <= interim_year:
        slope = (value_for_interim_year - value_for_start_year) / (interim_year - start_year)
        value = value_for_start_year + slope * (year - start_year)
    else:
        slope = (value_for_end_year - value_for_interim_year) / (end_year - interim_year)
        value = value_for_interim_year + slope * (year - interim_year)
    return value


def interpolate_cost(year, simulation_options, interpolation_data):
    start_year = simulation_options['start_year']
    interim_year = simulation_options['interim_year']
    end_year = simulation_options['end_year']

    start_value = interpolation_data.value_for_start_year
    end_value = interpolation_data.value_for_end_year
    interim_value = interpolation_data.value_for_interim_year
    _validate_interim_value(interim_value, start_value, end_value)

    if year <= interim_year:
        slope = (interim_value - start_value) / (interim_year - start_year)
        value = start_value + slope * (year - start_year)
    else:
        slope = (end_value - interim_value) / (end_year - interim_year)
        value = interim_value + slope * (year - interim_year)
    return value


def _validate_interim_value(interim_value, start_value, end_value):
    if interim_value is None:
        msg = 'interim_value must be provided for interpolate_cost'
        raise ValueError(msg)
    if start_value < end_value < interim_value:
        logging.warning(
            'interim_value %s is greater than end_value %s. Is this on purpose?',
            interim_value,
            end_value,
        )
    if end_value < start_value < interim_value:
        logging.warning(
            'interim_value %s is greater than start_value %s. Is this on purpose?',
            interim_value,
            start_value,
        )


def exponential_decrease(year, simulation_options, interpolation_data):
    start_year = simulation_options['start_year']
    interim_year = simulation_options['interim_year']
    end_year = simulation_options['end_year']

    start_value = interpolation_data.value_for_start_year
    end_value = interpolation_data.value_for_end_year
    interim_value = interpolation_data.value_for_interim_year
    _validate_interim_value(interim_value, start_value, end_value)

    if year <= interim_year:
        slope = (interim_value / start_value) ** (1 / (interim_year - start_year))
        value = start_value * slope ** (year - start_year)
    else:
        slope = (end_value - interim_value) / (end_year - interim_year)
        value = interim_value + slope * (year - interim_year)
    return value
