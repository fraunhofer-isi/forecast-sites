# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import random

from mesa.time import SimultaneousActivation


class TimeSchedule(SimultaneousActivation):
    """A scheduler to simulate the simultaneous activation of all the agents.

    This scheduler requires that each agent have two methods: step and advance.
    step() activates the agent and stages any necessary changes, but does not
    apply them yet. advance() then applies the changes.

    The time follows the passed time_span list

    """

    def __init__(self, model, time_span):
        super().__init__(model)
        self._time_span = time_span
        self.random = random.Random()
        if len(time_span) < 1:
            message = 'Time span must not be empty!'
            raise ValueError(message)
        self.time = time_span[0]
        self.previous_time = None
        self.steps = 0

    def step(self) -> None:
        """Step all agents, then advance them."""
        has_current_step = len(self._time_span) > self.steps
        if not has_current_step:
            message = 'Next step is not available. End of time span already reached'
            raise StopIteration(message)

        for agent in self._agents:
            agent.step()

        for agent in self._agents:
            agent.advance()

        has_next_step = len(self._time_span) > (self.steps + 1)
        self.steps += 1
        self.previous_time = self.time
        if has_next_step:
            self.time = self._time_span[self.steps]
        else:
            self.model.running = False
