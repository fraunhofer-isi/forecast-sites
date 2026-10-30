# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


def create_time_span(start_year, end_year, year_increment=1):
    """
    Build year anchors as list from start_year to end_year with given increment.

    Ensure end_year is included, even if not divisible by increment.
    """
    years = list(range(start_year, end_year + 1, year_increment))
    if years[-1] != end_year:
        years.append(end_year)
    return years


def to_year_strings(time_span):
    year_strings = map(_add_year_prefix, time_span)
    return list(year_strings)


def _add_year_prefix(year):
    return 'Y' + str(year)
