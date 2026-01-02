# © 2024-2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from simulation.simulation_mode import SimulationMode


def test_simulation_mode():
    enum_value = SimulationMode.DETERMINISTIC
    assert enum_value.value == 1
