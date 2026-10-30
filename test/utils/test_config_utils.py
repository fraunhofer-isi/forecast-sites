# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from datetime import UTC, datetime

import pytest
from test_utils.isi_mock import patch

from input.input_mode import InputMode
from optimization.optimization_type import OptimizationType
from utils import config_utils


@patch(config_utils._output_directory)
def test_simulation_options():
    simulation_options = config_utils.simulation_options()

    assert 'database_path' in simulation_options
    assert 'emission_constraint_scope' in simulation_options
    assert 'scenario_ids' in simulation_options
    assert 'output_directory' in simulation_options
    assert simulation_options['emission_constraint_scope'] == frozenset({'direct', 'upstream', 'renewably_bound', 'downstream'})
    scenario_ids = simulation_options['scenario_ids']
    assert isinstance(scenario_ids, list)
    assert all(isinstance(s, int) for s in scenario_ids)
    assert simulation_options['year_increment'] == 5


def test_post_process_options_csv_mode():
    """Test that CSV input mode overrides database path."""
    options = {
        'optimization_type': 'LINEAR_PROGRAMMING',
        'input_mode': 'CSV',
        'automatic_output_directory': False,
        'fixed_output_directory': 'output',
        'database_path': 'original_path.sqlite',
        'emission_constraint_scope': frozenset({'direct'}),
        'scenario_ids': [1],
    }

    with (
        patch(InputMode.from_string, return_value=InputMode.CSV),
        patch(OptimizationType.from_string, return_value=OptimizationType.LINEAR_PROGRAMMING),
        patch(config_utils._output_directory, return_value='mocked_output'),
    ):
        result = config_utils._post_process_options(options)

        # CSV mode should override database path
        assert result['database_path'] == './resources/input/input.sqlite'
        assert result['input_mode'] == InputMode.CSV


def test_post_process_options_non_csv_mode():
    """Test that non-CSV input mode preserves database path."""
    options = {
        'optimization_type': 'LINEAR_PROGRAMMING',
        'input_mode': 'SQLITE',
        'automatic_output_directory': False,
        'fixed_output_directory': 'output',
        'database_path': 'original_path.sqlite',
        'emission_constraint_scope': frozenset({'direct'}),
        'scenario_ids': [1],
    }

    with (
        patch(InputMode.from_string, return_value=InputMode.SQLITE),
        patch(OptimizationType.from_string, return_value=OptimizationType.LINEAR_PROGRAMMING),
        patch(config_utils._output_directory, return_value='mocked_output'),
    ):
        result = config_utils._post_process_options(options)

        # Non-CSV mode should preserve database path
        assert result['database_path'] == 'original_path.sqlite'
        assert result['input_mode'] == InputMode.SQLITE


class TestOutputDirectory:
    @patch(config_utils._database_name, 'mocked_database_name')
    @patch(config_utils._time_stamp, 'mocked_time_stamp')
    def test_automatic_output_directory(self):
        options = {
            'automatic_output_directory': True,
            'rolling_output_directory_prefix': 'prefix',
        }
        output_directory = config_utils._output_directory(options)
        assert output_directory == 'prefix_mocked_database_name_mocked_time_stamp'

    def test_fixed_output_directory(self):
        options = {
            'automatic_output_directory': False,
            'fixed_output_directory': 'fixed_directory',
        }
        output_directory = config_utils._output_directory(options)
        assert output_directory == 'fixed_directory'


def test_database_name():
    options = {
        'database_path': '/path/to/database_name.sqlite',
    }
    database_name = config_utils._database_name(options)
    assert database_name == 'database_name'


def test_time_stamp():
    options = {
        'rolling_output_directory_timestamp_format': '%Y%m%d_%H%M%S',
    }
    now = datetime.now(UTC)
    year = now.strftime('%Y')

    result = config_utils._time_stamp(options)
    assert year in result


def test_validated_emission_constraint_scope_legacy_direct_upstream_renewably_bound():
    """Test deprecated string format for emission scope - direct_upstream_renewably_bound."""
    options = {
        'emission_constraint_scope': 'direct_upstream_renewably_bound',
    }

    with patch(config_utils.logging.warning) as mock_warn:
        result = config_utils._validated_emission_constraint_scope(options)
        mock_warn.assert_called_once()
        assert result == frozenset({'direct', 'upstream', 'renewably_bound'})


def test_validated_emission_constraint_scope_legacy_all_components():
    """Test deprecated string format including downstream."""
    options = {
        'emission_constraint_scope': 'direct_upstream_renewably_bound_downstream',
    }

    with patch(config_utils.logging.warning) as mock_warn:
        result = config_utils._validated_emission_constraint_scope(options)
        mock_warn.assert_called_once()
        assert result == frozenset({'direct', 'upstream', 'renewably_bound', 'downstream'})


def test_validated_emission_constraint_scope_invalid_legacy_string():
    """Test error for unknown legacy string format."""
    options = {
        'emission_constraint_scope': 'unknown_scope',
    }

    with pytest.raises(ValueError, match='Unknown emission_constraint_scope'):
        config_utils._validated_emission_constraint_scope(options)


def test_validated_emission_constraint_scope_with_invalid_component():
    """Test error for invalid component in new list format."""
    options = {
        'emission_constraint_scope': ['direct', 'unknown_component'],
    }

    with pytest.raises(ValueError, match='Unknown emission_constraint_scope components'):
        config_utils._validated_emission_constraint_scope(options)


def test_valid_emission_constraint_scope_list_format():
    """Test valid list format for emission scope."""
    options = {
        'emission_constraint_scope': ['direct', 'upstream'],
    }

    result = config_utils._validated_emission_constraint_scope(options)

    assert result == frozenset({'direct', 'upstream'})


def test_validated_scenario_ids_accepts_list():
    """A list of scenario ids, like region_ids, passes through unchanged."""
    options = {'scenario_ids': [1, 3, 4]}

    result = config_utils._validated_scenario_ids(options)

    assert result == [1, 3, 4]


def test_validated_scenario_ids_rejects_bare_scalar():
    """A bare int (the pre-rename id_scenario = 1 style) is rejected, unlike region_ids.

    DECISION: scenario_ids requires a list, matching region_ids, rather than silently
    wrapping a scalar. See bd forecast-sites-private (scenario-id cleanup) for the
    discussion of why the old id_scenario key tolerated a bare scalar and this one does not.
    """
    options = {'scenario_ids': 1}

    with pytest.raises(ValueError, match='scenario_ids'):
        config_utils._validated_scenario_ids(options)


def test_warn_on_empty_emission_constraint_scope_with_limit():
    """Test warning when scope is empty but emission limit is set."""
    options = {
        'emission_constraint_scope': frozenset(),
        'emission_limit_in_t_co2': 50.0,
        'overall_emission_budget_in_t_co2': None,
    }

    with patch(config_utils.logging.warning) as mock_warn:
        config_utils._warn_on_empty_emission_constraint_scope(options)
        mock_warn.assert_called_once()


def test_warn_on_empty_emission_constraint_scope_with_budget():
    """Test warning when scope is empty but budget is set."""
    options = {
        'emission_constraint_scope': frozenset(),
        'emission_limit_in_t_co2': None,
        'overall_emission_budget_in_t_co2': 1000.0,
    }

    with patch(config_utils.logging.warning) as mock_warn:
        config_utils._warn_on_empty_emission_constraint_scope(options)
        mock_warn.assert_called_once()


def test_no_warn_on_empty_emission_constraint_scope_no_limits():
    """Test no warning when scope is empty and no limits set."""
    options = {
        'emission_constraint_scope': frozenset(),
        'emission_limit_in_t_co2': None,
        'overall_emission_budget_in_t_co2': None,
    }

    with patch(config_utils.logging.warning) as mock_warn:
        config_utils._warn_on_empty_emission_constraint_scope(options)
        mock_warn.assert_not_called()


def test_no_warn_on_empty_emission_constraint_scope_limit_is_infinite():
    """Test no warning when scope is empty and limit is practically infinite."""
    options = {
        'emission_constraint_scope': frozenset(),
        'emission_limit_in_t_co2': 1e50,
        'overall_emission_budget_in_t_co2': None,
    }

    with patch(config_utils.logging.warning) as mock_warn:
        config_utils._warn_on_empty_emission_constraint_scope(options)
        mock_warn.assert_not_called()


def test_no_warn_on_non_empty_emission_constraint_scope():
    """Test no warning when scope is not empty."""
    options = {
        'emission_constraint_scope': frozenset({'direct'}),
    }

    with patch(config_utils.logging.warning) as mock_warn:
        config_utils._warn_on_empty_emission_constraint_scope(options)
        mock_warn.assert_not_called()
