# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import Mock, fixture, patch

from optimization.linear_programming_optimization_result import (
    LinearProgrammingOptimizationResult,
)


@fixture
@patch(LinearProgrammingOptimizationResult._process_execution_counts)
@patch(LinearProgrammingOptimizationResult._purchased_carrier_amounts)
def sut():
    return LinearProgrammingOptimizationResult(
        'mocked_linear_programming_result',
        'mocked_processes',
        'mocked_carriers',
    )


def test_construction(sut):
    assert sut is not None


def test_process_execution_counts(sut):
    linear_programming_result = Mock()
    linear_programming_result.x = [10]
    processes = ['mocked_process']

    result = sut._process_execution_counts(linear_programming_result, processes)
    assert result == {'mocked_process': 10}


def test_carrier_amounts(sut):
    linear_programming_result = Mock()
    linear_programming_result.x = [10, 20]
    processes = ['mocked_process_1']
    carriers = ['mocked_carrier_1']

    result = sut._purchased_carrier_amounts(linear_programming_result, processes, carriers)
    assert result == {'mocked_carrier_1': 20}
