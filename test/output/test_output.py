# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest
from test_utils.isi_mock import Mock, fixture

from output.output import Output

mocked_carrier = Mock()


@fixture
def sut():
    return Output(mocked_carrier)


def test_construction(sut):
    assert sut is not None


def test_carrier(sut):
    assert sut.carrier == mocked_carrier


def test__repr__(sut):
    with pytest.raises(NotImplementedError):
        sut.__repr__()


def test_accept(sut):
    visitor = Mock()
    sut.accept(visitor, 2023)
    assert visitor.enter_output.called
    assert visitor.exit_output.called


def test_sell_gain_in_euro_per_process_count(sut):
    with pytest.raises(NotImplementedError):
        sut.output_in_euro_per_process_count(2023, 100, {'start_year': 2000})
