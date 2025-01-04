# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# assertion module you can import tests from
import numpy as np
from pytest import approx


def truthy(value):
    return bool(value)


def falsy(value):
    return not bool(value)


def assert_sum_of_all_values_in_dataframe(result, value):
    assert approx(value, 0.001) == result.values.sum()


def allow_strings_but_no_nan_or_inf_values(matrix):
    # allow strings
    # do not allow nan, -inf, inf
    for row in matrix:
        for value in row:
            is_no_string = not isinstance(value, str)
            if is_no_string:
                assert np.isfinite(value)
