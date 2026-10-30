# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import fixture

from optimization.linear_programming_constraint import LinearProgrammingConstraint


@fixture
def sut():
    number_of_processes = 3
    number_of_carriers = 3
    reference_value = 100
    return LinearProgrammingConstraint(number_of_processes, number_of_carriers, reference_value, 'mocked_label')


def test_construction(sut):
    assert sut is not None


def test__repr__(sut):
    result = str(sut)
    assert result == 'LinearProgrammingConstraint(||[0, 0, 0]|[0, 0, 0] ||100||mocked_label)'


def test_matrix_coefficients(sut):
    result = sut.matrix_coefficients
    assert result == [0, 0, 0, 0, 0, 0]
