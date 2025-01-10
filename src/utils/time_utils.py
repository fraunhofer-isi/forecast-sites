# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def create_time_span(start_year, end_year, year_increment):
    return list(range(start_year, end_year + 1, year_increment))


def to_year_strings(time_span):
    year_strings = map(_add_year_prefix, time_span)
    return list(year_strings)


def _add_year_prefix(year):
    return "Y" + str(year)


def interpolate(year, value_2015, value_2050):
    slope = (value_2050 - value_2015) / (2050 - 2022)
    value = value_2015 + slope * (year - 2022)
    return value


def interpolate_cost(year, value_2015, value_2030, value_2050):
    year_threshold = 2030
    if year <= year_threshold:
        slope = (value_2030 - value_2015) / (year_threshold - 2022)
        value = value_2015 + slope * (year - 2022)
    else:
        slope = (value_2050 - value_2030) / (2050 - year_threshold)
        value = value_2030 + slope * (year - year_threshold)
    return value


def exponential_decrease(year, value_2015, value_2030, value_2050):
    year_threshold = 2030
    if year <= year_threshold:
        slope = (value_2030 / value_2015) ** (1 / (year_threshold - 2022))
        value = value_2015 * slope ** (year - 2022)
    else:
        slope = (value_2050 - value_2030) / (2050 - year_threshold)
        value = value_2030 + slope * (year - year_threshold)
    return value
