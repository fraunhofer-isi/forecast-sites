# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from mock import MagicMock

from mesa_wrapper.time_schedule import TimeSchedule


@pytest.fixture
def sut():
    return TimeSchedule(model=MagicMock(), time_span=[2020, 2022])


def test_init_with_empty_timespan():
    with pytest.raises(ValueError):
        TimeSchedule(model=MagicMock(), time_span=[])


class TestStep:

    def test_normal_usage(self, sut):
        agent_mock = MagicMock()
        sut._agents = {'foo': agent_mock}
        assert sut.time == 2020
        sut.step()
        assert agent_mock.step.called
        assert agent_mock.advance.called
        assert sut.time == 2022
        assert sut.previous_time == 2020

    def test_step_limit_exceeded(self, sut):
        agent_mock = MagicMock()
        sut._agents = {'foo': agent_mock}
        assert sut.time == 2020
        sut.step()
        assert sut.time == 2022
        sut.step()
        with pytest.raises(StopIteration):
            sut.step()
