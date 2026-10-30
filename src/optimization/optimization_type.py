# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from enum import StrEnum


class OptimizationType(StrEnum):
    LINEAR_PROGRAMMING = 'LINEAR_PROGRAMMING'

    COMPARING = 'COMPARING'
    REGION_MULTI_PERIOD = 'REGION_MULTI_PERIOD'

    @property
    def is_region_scoped(self):
        return self == OptimizationType.REGION_MULTI_PERIOD

    @staticmethod
    def from_string(type_as_string):
        for optimization_type in OptimizationType:
            if optimization_type.value == type_as_string:
                return optimization_type
        message = f'Unknown optimization type: {type_as_string}'
        raise ValueError(message)
