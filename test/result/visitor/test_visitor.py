# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import fixture, original_patch, patch

from result import aggregation
from result.visitor.visitor import Visitor


@fixture
@original_patch.multiple(Visitor, __abstractmethods__=set())
def sut():
    return Visitor()


def test_construction(sut):
    assert sut is not None


def test_enter_region(sut):
    with pytest.raises(NotImplementedError):
        sut.enter_region('mocked_region', 2020)


@patch(aggregation.aggregate_dictionaries, 'mocked_result')
def test_exit_region(sut):
    result = sut.exit_region(
        'mocked_region',
        2020,
        'mocked_enter_results',
        'mocked_site_results',
    )
    assert result == 'mocked_result'


def test_enter_site(sut):
    sut.enter_site('mocked_site', 2020)
    assert True


@patch(aggregation.aggregate_dictionaries, 'mocked_result')
def test_exit_site(sut):
    result = sut.exit_site(
        'mocked_site',
        2020,
        'mocked_enter_results',
        'mocked_production_unit_results',
    )
    assert result == 'mocked_result'


def test_enter_production_unit(sut):
    sut.enter_production_unit('mocked_production_unit', 2020)
    assert True


@patch(aggregation.aggregate_dictionaries, 'mocked_result')
def test_exit_production_unit(sut):
    result = sut.exit_production_unit(
        'mocked_production_unit',
        2020,
        'mocked_enter_results',
        'mocked_sub_production_unit_results',
    )
    assert result == 'mocked_result'


def test_enter_sub_production_unit(sut):
    sut.enter_sub_production_unit('mocked_sub_production_unit', 2020)
    assert True


def test_exit_sub_production_unit(sut):
    result = sut.exit_sub_production_unit(
        'mocked_sub_production_unit',
        2020,
        'mocked_enter_results',
        'mocked_process_result',
    )
    assert result == 'mocked_process_result'


def test_enter_process(sut):
    sut.enter_process('mocked_process', 2020)
    assert True


@patch(aggregation.aggregate_dictionaries, {'mocked_aggregated_result': 10})
def test_exit_process(sut):
    enter_results = {}
    result = sut.exit_process(
        'mocked_process',
        2020,
        enter_results,
        'mocked_output_results',
    )
    assert result['mocked_aggregated_result'] == 10


def test_enter_output(sut):
    sut.enter_output('mocked_output', 2020)
    assert True


def test_exit_output(sut):
    result = sut.exit_output(
        'mocked_output',
        2020,
        'mocked_enter_results',
    )
    assert result == {}


def test_finalize(sut):
    sut.finalize()
    assert True
