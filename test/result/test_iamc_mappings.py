# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

import pandas as pd
import pytest

from result.iamc_mappings import (
    FORECAST_MODEL_NAME,
    ISO_CODE_LENGTH,
    REGION_NAME_TO_IAMC_CODE,
    region_name_to_iamc_code,
    resolve_scenario_name,
)


class TestConstants:
    """Tests for module constants."""

    def test_forecast_model_name(self) -> None:
        """FORECAST_MODEL_NAME constant is correct."""
        assert FORECAST_MODEL_NAME == 'FORECAST'

    def test_iso_code_length(self) -> None:
        """ISO_CODE_LENGTH constant is 2."""
        assert ISO_CODE_LENGTH == 2

    def test_region_name_to_iamc_code_dict_exists(self) -> None:
        """REGION_NAME_TO_IAMC_CODE dictionary exists and contains data."""
        assert isinstance(REGION_NAME_TO_IAMC_CODE, dict)
        assert len(REGION_NAME_TO_IAMC_CODE) > 0

    def test_region_mapping_has_required_countries(self) -> None:
        """REGION_NAME_TO_IAMC_CODE contains expected EU countries."""
        required = ['Austria', 'Germany', 'France', 'Poland', 'Italy']
        for country in required:
            assert country in REGION_NAME_TO_IAMC_CODE

    def test_region_mapping_codes_are_iso_2_letter(self) -> None:
        """All region mappings are 2-letter ISO codes."""
        for code in REGION_NAME_TO_IAMC_CODE.values():
            assert len(code) == 2
            assert code.isupper()

    def test_region_mapping_austria_to_at(self) -> None:
        """Austria maps to AT."""
        assert REGION_NAME_TO_IAMC_CODE['Austria'] == 'AT'

    def test_region_mapping_germany_to_de(self) -> None:
        """Germany maps to DE."""
        assert REGION_NAME_TO_IAMC_CODE['Germany'] == 'DE'

    def test_region_mapping_has_czechia_variant(self) -> None:
        """Both Czech Republic and Czechia map to CZ."""
        assert REGION_NAME_TO_IAMC_CODE['Czech Republic'] == 'CZ'
        assert REGION_NAME_TO_IAMC_CODE['Czechia'] == 'CZ'


class TestRegionNameToIamcCode:
    """Tests for region_name_to_iamc_code function."""

    def test_converts_austria_to_at(self) -> None:
        """Converts 'Austria' to 'AT'."""
        result = region_name_to_iamc_code('Austria')

        assert result == 'AT'

    def test_converts_germany_to_de(self) -> None:
        """Converts 'Germany' to 'DE'."""
        result = region_name_to_iamc_code('Germany')

        assert result == 'DE'

    def test_converts_all_mapped_regions(self) -> None:
        """Converts all mapped region names."""
        for region, code in REGION_NAME_TO_IAMC_CODE.items():
            result = region_name_to_iamc_code(region)
            assert result == code

    def test_passes_through_iso_code(self) -> None:
        """Passes through 2-letter uppercase ISO codes."""
        result = region_name_to_iamc_code('AT')

        assert result == 'AT'

    def test_passes_through_various_iso_codes(self) -> None:
        """Passes through various ISO codes without lookup."""
        iso_codes = ['AT', 'DE', 'FR', 'GB', 'NO', 'CH']
        for iso in iso_codes:
            result = region_name_to_iamc_code(iso)
            assert result == iso

    def test_strips_whitespace(self) -> None:
        """Strips whitespace from region names."""
        result = region_name_to_iamc_code('  Austria  ')

        assert result == 'AT'

    def test_strips_whitespace_and_converts(self) -> None:
        """Strips whitespace, then converts name."""
        result = region_name_to_iamc_code('\tGermany\n')

        assert result == 'DE'

    def test_raises_keyerror_for_unknown_region(self) -> None:
        """Raises KeyError for unknown region names."""
        with pytest.raises(KeyError, match='No IAMC region mapping'):
            region_name_to_iamc_code('UnknownRegion')

    def test_raises_keyerror_for_typo(self) -> None:
        """Raises KeyError for misspelled region names."""
        with pytest.raises(KeyError):
            region_name_to_iamc_code('Germanyy')  # Typo

    def test_raises_keyerror_for_empty_string(self) -> None:
        """Raises KeyError for empty string."""
        with pytest.raises(KeyError):
            region_name_to_iamc_code('')

    def test_raises_keyerror_for_single_letter(self) -> None:
        """Raises KeyError for single-letter codes (not ISO 2-letter)."""
        with pytest.raises(KeyError):
            region_name_to_iamc_code('A')

    def test_raises_keyerror_for_lowercase_iso(self) -> None:
        """Raises KeyError for lowercase ISO codes."""
        with pytest.raises(KeyError):
            region_name_to_iamc_code('at')

    def test_error_message_includes_region_name(self) -> None:
        """Error message includes the requested region name."""
        with pytest.raises(KeyError) as exc_info:
            region_name_to_iamc_code('InvalidRegion')

        assert 'InvalidRegion' in str(exc_info.value)

    def test_does_not_convert_three_letter_codes(self) -> None:
        """Does not convert 3-letter codes."""
        with pytest.raises(KeyError):
            region_name_to_iamc_code('AUT')

    def test_handles_whitespace_only_string(self) -> None:
        """Raises KeyError for whitespace-only string."""
        with pytest.raises(KeyError):
            region_name_to_iamc_code('   ')

    def test_case_sensitive_for_region_names(self) -> None:
        """Region name lookup is case-sensitive."""
        with pytest.raises(KeyError):
            region_name_to_iamc_code('austria')  # Lowercase

    def test_uk_mapping(self) -> None:
        """United Kingdom maps to GB."""
        result = region_name_to_iamc_code('United Kingdom')

        assert result == 'GB'

    def test_czechia_alternate_name(self) -> None:
        """Czechia (modern name) maps to CZ."""
        result = region_name_to_iamc_code('Czechia')

        assert result == 'CZ'


class TestResolveScenarioName:
    """Tests for resolve_scenario_name function."""

    def test_returns_name_from_dataframe(self) -> None:
        """Returns scenario name from scenario_df."""
        scenario_df = pd.DataFrame(
            {
                'id': [1, 2, 3],
                'name': ['Baseline', 'Green', 'Brown'],
            }
        )

        result = resolve_scenario_name(1, scenario_df)

        assert result == 'Baseline'

    def test_returns_matching_scenario_by_id(self) -> None:
        """Finds and returns correct scenario by id."""
        scenario_df = pd.DataFrame(
            {
                'id': [1, 2, 3],
                'name': ['Baseline', 'Green', 'Brown'],
            }
        )

        result = resolve_scenario_name(2, scenario_df)

        assert result == 'Green'

    def test_returns_last_scenario_id_when_no_df(self) -> None:
        """Returns id_scenario as string when no dataframe."""
        result = resolve_scenario_name(42, None)

        assert result == '42'

    def test_returns_id_when_dataframe_empty(self) -> None:
        """Returns id_scenario as string when dataframe is empty."""
        scenario_df = pd.DataFrame(columns=['id', 'name'])

        result = resolve_scenario_name(99, scenario_df)

        assert result == '99'

    def test_returns_id_when_no_match_in_dataframe(self) -> None:
        """Returns id_scenario as string when no matching row."""
        scenario_df = pd.DataFrame(
            {
                'id': [1, 2, 3],
                'name': ['Baseline', 'Green', 'Brown'],
            }
        )

        result = resolve_scenario_name(999, scenario_df)

        assert result == '999'

    def test_converts_integer_name_to_string(self) -> None:
        """Converts integer name values to string."""
        scenario_df = pd.DataFrame(
            {
                'id': [1],
                'name': [123],
            }
        )

        result = resolve_scenario_name(1, scenario_df)

        assert isinstance(result, str)
        assert result == '123'

    def test_preserves_string_name(self) -> None:
        """Preserves string names as-is."""
        scenario_df = pd.DataFrame(
            {
                'id': [1],
                'name': ['ScenarioA'],
            }
        )

        result = resolve_scenario_name(1, scenario_df)

        assert result == 'ScenarioA'

    def test_with_multiple_scenarios_returns_first_match(self) -> None:
        """Returns first matching scenario when multiple rows with same id."""
        scenario_df = pd.DataFrame(
            {
                'id': [1, 1, 2],
                'name': ['First', 'Second', 'Third'],
            }
        )

        result = resolve_scenario_name(1, scenario_df)

        # iloc[0] should return 'First'
        assert result == 'First'

    def test_with_dataframe_none_and_id_provided(self) -> None:
        """Returns string id when dataframe is None but id provided."""
        result = resolve_scenario_name(5, None)

        assert result == '5'

    def test_with_extra_columns_in_dataframe(self) -> None:
        """Works correctly with extra columns in dataframe."""
        scenario_df = pd.DataFrame(
            {
                'id': [1],
                'name': ['Baseline'],
                'description': ['This is baseline'],
                'year': [2020],
            }
        )

        result = resolve_scenario_name(1, scenario_df)

        assert result == 'Baseline'

    def test_name_with_special_characters(self) -> None:
        """Handles scenario names with special characters."""
        scenario_df = pd.DataFrame(
            {
                'id': [1],
                'name': ['Green-2050 (High)'],
            }
        )

        result = resolve_scenario_name(1, scenario_df)

        assert result == 'Green-2050 (High)'

    def test_id_scenario_as_integer(self) -> None:
        """Works with integer id_scenario value."""
        scenario_df = pd.DataFrame(
            {
                'id': [42],
                'name': ['Custom Scenario'],
            }
        )

        result = resolve_scenario_name(42, scenario_df)

        assert result == 'Custom Scenario'

    def test_id_scenario_as_float_converted_to_string(self) -> None:
        """Converts float id_scenario to string."""
        result = resolve_scenario_name(3.14, None)

        assert result == '3.14'


class TestResolveScenarioNameEdgeCases:
    """Edge cases for resolve_scenario_name."""

    def test_very_large_id_scenario(self) -> None:
        """Handles very large id_scenario values."""
        result = resolve_scenario_name(999999999, None)

        assert result == '999999999'

    def test_negative_id_scenario(self) -> None:
        """Handles negative id_scenario values."""
        result = resolve_scenario_name(-1, None)

        assert result == '-1'

    def test_zero_id_scenario(self) -> None:
        """Handles zero as id_scenario."""
        result = resolve_scenario_name(0, None)

        assert result == '0'

    def test_dataframe_with_nan_names(self) -> None:
        """Handles DataFrames with NaN in name column."""
        scenario_df = pd.DataFrame(
            {
                'id': [1, 2],
                'name': ['Baseline', None],
            }
        )

        result = resolve_scenario_name(2, scenario_df)

        # pandas converts None to NaN; str(NaN) can be 'nan' or 'None' depending on version
        assert result in ('None', 'nan')

    def test_dataframe_with_numeric_id_column(self) -> None:
        """Works with numeric id column."""
        scenario_df = pd.DataFrame(
            {
                'id': [100, 200, 300],
                'name': ['S1', 'S2', 'S3'],
            }
        )

        result = resolve_scenario_name(200, scenario_df)

        assert result == 'S2'


class TestIamcMappingsIntegration:
    """Integration tests for iamc_mappings module."""

    def test_workflow_region_and_scenario(self) -> None:
        """Integration: map region and resolve scenario."""
        region = region_name_to_iamc_code('Germany')

        scenario_df = pd.DataFrame(
            {
                'id': [1, 2],
                'name': ['Baseline', 'Green'],
            }
        )
        scenario = resolve_scenario_name(2, scenario_df)

        assert region == 'DE'
        assert scenario == 'Green'

    def test_all_regions_mappable(self) -> None:
        """All regions in the mapping dictionary are convertible."""
        for region_name in REGION_NAME_TO_IAMC_CODE:
            result = region_name_to_iamc_code(region_name)
            assert len(result) == 2
            assert result.isupper()

    def test_forecast_model_name_constant(self) -> None:
        """FORECAST_MODEL_NAME is available for export workflows."""
        assert FORECAST_MODEL_NAME == 'FORECAST'
        assert isinstance(FORECAST_MODEL_NAME, str)
        assert len(FORECAST_MODEL_NAME) > 0
