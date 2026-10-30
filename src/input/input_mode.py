# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from enum import StrEnum


class InputMode(StrEnum):
    SQLITE = 'SQLITE'
    CSV = 'CSV'

    @staticmethod
    def from_string(type_as_string):
        for mode in InputMode:
            if mode.value == type_as_string:
                return mode
        message = f'Unknown input mode: {type_as_string}'
        raise ValueError(message)
