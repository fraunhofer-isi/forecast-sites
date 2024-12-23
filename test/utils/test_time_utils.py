# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from math import isclose

from utils.time_utils import (
    create_time_span,
    exponential_decrease,
    interpolate,
    interpolate_cost,
    to_year_strings,
)


def test_create_time_span():
    time_span = create_time_span(2015, 2017)
    assert time_span == [2015, 2016, 2017]


def test_create_time_span_increment():
    time_span = create_time_span(2015, 2024, 3)
    assert time_span == [2015, 2018, 2021, 2024]


def test_to_year_strings():
    time_span = range(2015, 2018, 1)
    year_strings = to_year_strings(time_span)
    assert year_strings == ['Y2015', 'Y2016', 'Y2017']


def test_interpolate():
    value_2015 = 2
    value_2050 = 20
    year = 2025
    result = interpolate(year, value_2015, value_2050)
    assert isclose(result, 50 / 7)


def test_interpolate_cost():
    value_2015 = 2
    value_2030 = 10
    value_2050 = 20
    year = 2025
    result = interpolate_cost(year, value_2015, value_2030, value_2050)
    assert isclose(result, 5)


def test_exponential_decrease():
    value_2015 = 2
    value_2030 = 10
    value_2050 = 20
    year = 2025
    result = interpolate_cost(year, value_2015, value_2030, value_2050)
    assert isclose(result, 29.3558735)
