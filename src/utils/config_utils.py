# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging
from datetime import UTC, datetime
from pathlib import Path

import toml

from input.input_mode import InputMode
from optimization.optimization_type import OptimizationType

DEFAULT_EMISSION_CONSTRAINT_SCOPE = frozenset({'direct', 'upstream', 'renewably_bound'})
SUPPORTED_EMISSION_CONSTRAINT_SCOPE_COMPONENTS = frozenset(
    {
        'direct',
        'upstream',
        'renewably_bound',
        'downstream',
    }
)
LEGACY_EMISSION_CONSTRAINT_SCOPES = {
    'direct_upstream_renewably_bound': DEFAULT_EMISSION_CONSTRAINT_SCOPE,
    'direct_upstream_renewably_bound_downstream': frozenset(
        {
            'direct',
            'upstream',
            'renewably_bound',
            'downstream',
        }
    ),
}
PRACTICALLY_INFINITE_EMISSION_LIMIT_IN_T_CO2 = 1e50


def simulation_options():
    file_path = Path(__file__).parent.parent / 'simulation_options.toml'
    with Path(file_path).open('r', encoding='utf-8') as file:
        options = toml.load(file)
        options = post_process_options(options)

    return options


def post_process_options(options):
    return _post_process_options(options)


def _post_process_options(options):
    options['optimization_type'] = OptimizationType.from_string(options['optimization_type'])
    options['input_mode'] = InputMode.from_string(options['input_mode'])
    options['emission_constraint_scope'] = _validated_emission_constraint_scope(options)
    _warn_on_empty_emission_constraint_scope(options)
    options['scenario_ids'] = _validated_scenario_ids(options)
    options['output_directory'] = _output_directory(options)

    if options['input_mode'] == InputMode.CSV:
        # override database path, so that csv import does not override other existing databases
        options['database_path'] = './resources/input/input.sqlite'

    return options


def _validated_scenario_ids(options):
    scenario_ids = options['scenario_ids']
    if not isinstance(scenario_ids, list):
        message = f"'scenario_ids' must be a list, like 'region_ids'. Got {type(scenario_ids).__name__}: {scenario_ids!r}."
        raise ValueError(message)
    return scenario_ids


def _validated_emission_constraint_scope(options):
    emission_constraint_scope = options.get('emission_constraint_scope', DEFAULT_EMISSION_CONSTRAINT_SCOPE)

    if isinstance(emission_constraint_scope, str):
        legacy_scope = LEGACY_EMISSION_CONSTRAINT_SCOPES.get(emission_constraint_scope)
        if legacy_scope is not None:
            logging.warning(
                'Deprecated string emission_constraint_scope %s. Use list format instead.',
                emission_constraint_scope,
            )
            return legacy_scope
        supported_scopes = ', '.join(sorted(LEGACY_EMISSION_CONSTRAINT_SCOPES))
        message = f'Unknown emission_constraint_scope: {emission_constraint_scope}. Supported legacy values: {supported_scopes}'
        raise ValueError(message)

    normalized_scope = frozenset(emission_constraint_scope)
    unknown_components = normalized_scope - SUPPORTED_EMISSION_CONSTRAINT_SCOPE_COMPONENTS
    if not unknown_components:
        return normalized_scope

    supported_components = ', '.join(sorted(SUPPORTED_EMISSION_CONSTRAINT_SCOPE_COMPONENTS))
    message = (
        f'Unknown emission_constraint_scope components: {sorted(unknown_components)}. '
        f'Supported components: {supported_components}'
    )
    raise ValueError(message)


def _warn_on_empty_emission_constraint_scope(options):
    if options['emission_constraint_scope']:
        return

    emission_limit = options.get('emission_limit_in_t_co2')
    overall_emission_budget = options.get('overall_emission_budget_in_t_co2')
    if overall_emission_budget is None and (
        emission_limit is None or emission_limit >= PRACTICALLY_INFINITE_EMISSION_LIMIT_IN_T_CO2
    ):
        return

    logging.warning(
        'emission_constraint_scope is empty while emission limits or budgets are set. '
        'Emission constraints and budget accounting will be trivially satisfied.'
    )


def _output_directory(options):
    automatic_output_directory = options['automatic_output_directory']
    if automatic_output_directory:
        prefix = options['rolling_output_directory_prefix']
        database_name = _database_name(options)
        timestamp = _time_stamp(options)
        output_directory = f'{prefix}_{database_name}_{timestamp}'
    else:
        output_directory = options['fixed_output_directory']
    return output_directory


def _database_name(options):
    database_path = options['database_path']
    database_name = Path(database_path).stem
    return database_name


def _time_stamp(options) -> str:
    time_stamp_format = options['rolling_output_directory_timestamp_format']
    timestamp = datetime.now(tz=UTC).strftime(time_stamp_format)
    return timestamp
