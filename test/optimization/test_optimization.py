# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import Mock, fixture

from optimization.optimization import Optimization


@fixture
def sut():
    year = 2015
    production_unit = Mock()
    context = Mock()
    return Optimization(
        year,
        production_unit,
        context,
    )


def test_construction(sut):
    assert sut is not None


def test_optimize(sut):
    with pytest.raises(NotImplementedError):
        sut.optimize()


def test_process_options(sut):
    result = sut._process_options
    assert result == sut._production_unit.available_process_options


def test_carriers(sut):
    result = sut._carriers
    assert result == sut._production_unit.available_carriers


def test_number_of_process_options(sut):
    result = sut.number_of_process_options
    assert result == len(sut._production_unit.available_process_options)


def test_number_of_carriers(sut):
    result = sut.number_of_carriers
    assert result == len(sut._production_unit.available_carriers)
