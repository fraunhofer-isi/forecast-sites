# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from optimization.comparing_optimization import ComparingOptimization
from optimization.linear_programming_optimization import LinearProgrammingOptimization
from optimization.optimization_type import OptimizationType


class OptimizationFactory:
    def __init__(self, optimization_type):
        self._type = optimization_type

    def create(self, year, production_unit, context):
        if not isinstance(self._type, OptimizationType):
            message = f'Unknown optimization type {self._type}'
            raise ValueError(message)

        if self._type.is_region_scoped:
            msg = (
                f'Optimization type {self._type} requires region-scoped dispatch. '
                f'It cannot be used with per-production-unit optimization.'
            )
            raise ValueError(msg)
        self._validate_supported_simulation_options(context)

        if self._type == OptimizationType.LINEAR_PROGRAMMING:
            return LinearProgrammingOptimization(year, production_unit, context)
        if self._type == OptimizationType.COMPARING:
            return ComparingOptimization(year, production_unit, context)
        message = f'Unknown optimization type {self._type}'
        raise ValueError(message)

    def _validate_supported_simulation_options(self, context):
        simulation_options = context.simulation_options
        overall_emission_budget = simulation_options.get('overall_emission_budget_in_t_co2')

        if overall_emission_budget is None:
            return

        if self._type == OptimizationType.REGION_MULTI_PERIOD:
            return

        message = (
            'overall_emission_budget_in_t_co2 is only supported for REGION_MULTI_PERIOD optimization. '
            f'Current optimization type: {self._type}'
        )
        raise ValueError(message)
