# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

FORECAST_MODEL_NAME = 'FORECAST'

REGION_NAME_TO_IAMC_CODE = {
    'Austria': 'AT',
    'Belgium': 'BE',
    'Bulgaria': 'BG',
    'Croatia': 'HR',
    'Czech Republic': 'CZ',
    'Czechia': 'CZ',
    'Denmark': 'DK',
    'Estonia': 'EE',
    'Finland': 'FI',
    'France': 'FR',
    'Germany': 'DE',
    'Greece': 'GR',
    'Hungary': 'HU',
    'Ireland': 'IE',
    'Italy': 'IT',
    'Latvia': 'LV',
    'Lithuania': 'LT',
    'Luxembourg': 'LU',
    'Netherlands': 'NL',
    'Norway': 'NO',
    'Poland': 'PL',
    'Portugal': 'PT',
    'Romania': 'RO',
    'Slovakia': 'SK',
    'Slovenia': 'SI',
    'Spain': 'ES',
    'Sweden': 'SE',
    'Switzerland': 'CH',
    'United Kingdom': 'GB',
}


ISO_CODE_LENGTH = 2


def region_name_to_iamc_code(region_name: str) -> str:
    # Region names may use underscores instead of spaces; normalize before lookup.
    normalized_name = region_name.strip().replace('_', ' ')
    if len(normalized_name) == ISO_CODE_LENGTH and normalized_name.isupper():
        return normalized_name

    iamc_code = REGION_NAME_TO_IAMC_CODE.get(normalized_name)
    if iamc_code is None:
        msg = f"No IAMC region mapping configured for '{region_name}'."
        raise KeyError(msg)
    return iamc_code


def resolve_scenario_name(id_scenario: int, scenario_df: pd.DataFrame | None) -> str:
    """Resolve the human-readable scenario name, falling back to id_scenario's string form."""
    if scenario_df is not None and not scenario_df.empty:
        matching_rows = scenario_df[scenario_df['id'] == id_scenario]
        if not matching_rows.empty:
            return str(matching_rows.iloc[0]['name'])

    return str(id_scenario)
