# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from enum import Enum


class SimulationMode(Enum):
    DETERMINISTIC = 1
    MONTE_CARLO = 2
