# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import fixture

from mesa_wrapper.simulation_factory import SimulationFactory


class DemoClass:
    def __init__(self, foo):
        self.foo = foo


@fixture
def sut():
    return SimulationFactory(DemoClass)


def test_construction(sut):
    assert sut is not None


def test_singleton_behavior(sut):
    instance1 = sut('1')
    instance2 = sut('2')
    assert instance1 is instance2
    assert instance2.foo == '1'
