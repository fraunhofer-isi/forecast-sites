# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from immutable.immutable import Immutable


class InterpolationData(Immutable):
    def __init__(
        self,
        value_for_start_year,
        value_for_end_year,
        value_for_interim_year=None,
    ):
        self.value_for_start_year = value_for_start_year
        self.value_for_end_year = value_for_end_year
        self.value_for_interim_year = value_for_interim_year
        self._initialized_immutability = True
