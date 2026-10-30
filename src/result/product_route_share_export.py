# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from result.iamc_formatter import (
    IamcExportConfig,
    build_iamc_long_table,
    pivot_iamc_wide_table,
    save_iamc_table,
)
from result.iamc_mappings import (
    FORECAST_MODEL_NAME,
    region_name_to_iamc_code,
    resolve_scenario_name,
)
from route_analysis.upstream_chain_builder import UpstreamChain, UpstreamChainBuilder
from utils.time_utils import create_time_span

AMMONIA_PRODUCT_ID = 501
METHANOL_PRODUCT_ID = 546
OTHER_ROUTE = 'Other'
ROUTE_MIN_VALUE = 1e-9
TONS_PER_MEGATON = 1_000_000.0

PRODUCT_LABELS = {
    AMMONIA_PRODUCT_ID: 'Ammonia',
    METHANOL_PRODUCT_ID: 'Methanol',
}

PRODUCT_ROUTE_DEFINITIONS: dict[int, dict[str, set[int]]] = {
    AMMONIA_PRODUCT_ID: {
        'SMR': {5120},
        'SMR + CCS': {5130},
        'Biomass gasification': {5140},
        'Biomass gasification + CCS': {5150},
        'Hydrogen-derived': {5110, 5160, 5170},
        'ATR-derived': {5710},
        'Imported hydrogen-derived': set(),
    },
    METHANOL_PRODUCT_ID: {
        'SMR-derived': {5440},
        'ATR-derived': {5710},
        'Hydrogen-derived': {5110, 5160, 5170, 5412, 5430},
        'Biomass gasification-derived': {5520, 5421},
        'Waste gasification-derived': {5510, 5422},
        'Imported methanol': set(),
    },
}

PURCHASE_ROUTE_DEFINITIONS: dict[int, dict[str, dict[str, set[int]]]] = {
    AMMONIA_PRODUCT_ID: {
        'Imported hydrogen-derived': {
            'carrier_ids': {26, 1026},
            'product_ids': set(),
        }
    },
    METHANOL_PRODUCT_ID: {
        'Imported methanol': {
            'carrier_ids': {54, 1054},
            'product_ids': {METHANOL_PRODUCT_ID},
        }
    },
}

CHAIN_TABLE_NAMES = [
    'process_product_production_in_t',
    'process_by_product_production_in_t',
    'process_energy_carrier_production_in_gj',
    'process_energy_carrier_energy_demand_in_gj',
    'process_energy_carrier_feedstock_demand_in_gj',
    'process_product_feedstock_demand_in_t',
    'process_by_product_feedstock_demand_in_t',
    'production_unit_energy_carrier_purchased_amount_in_gj',
    'production_unit_product_purchased_amount_in_t',
    'production_unit_by_product_purchased_amount_in_t',
    'energy_carrier_lower_heating_value_in_gj_per_t',
]
REGION_TABLE_NAME = 'id_region'
SCENARIO_TABLE_NAME = 'id_scenario'


@dataclass
class _TableContext:
    tables: dict[str, pd.DataFrame]

    def get(self, key: str):
        return self.tables.get(key)


def export_product_route_shares(id_scenario: int, simulation_options) -> None:
    output_directory = simulation_options['output_directory']
    output_path = Path(output_directory)
    database_path = output_path / 'output.sqlite'
    if not database_path.is_file():
        msg = f"The database file '{database_path}' does not exist."
        raise FileNotFoundError(msg)

    years = create_time_span(
        simulation_options['start_year'],
        simulation_options['end_year'],
        simulation_options['year_increment'],
    )
    tables = _read_chain_tables(database_path)
    scenario_name = resolve_scenario_name(id_scenario, tables.get(SCENARIO_TABLE_NAME))
    region_names = _region_name_map(tables.get(REGION_TABLE_NAME))
    region_ids = _region_ids_for_export(tables, id_scenario)

    production_rows = []
    share_rows = []
    for region_id in region_ids:
        filtered_tables = _filter_tables_for_region(tables, region_id, scenario_id=id_scenario)
        region_name = region_names.get(region_id, f'Region {region_id}')
        for product_id in PRODUCT_ROUTE_DEFINITIONS:
            production_rows.extend(
                _build_product_rows(
                    region_name,
                    scenario_name,
                    product_id,
                    years,
                    filtered_tables,
                    value_kind='production_in_t',
                )
            )
            share_rows.extend(
                _build_product_rows(
                    region_name,
                    scenario_name,
                    product_id,
                    years,
                    filtered_tables,
                    value_kind='share_in_percent',
                )
            )

    _save_iamc_production_table(
        production_rows,
        output_path,
        'product_route_production_by_region_in_t',
        scenario_name,
    )
    _save_wide_table(
        share_rows,
        output_path,
        'product_route_share_by_region_in_percent',
        'share_in_percent',
        index_columns=['scenario', 'region', 'product', 'route'],
    )


def _build_product_rows(
    region_name: str,
    scenario_name: str,
    product_id: int,
    years: list[int],
    tables: dict[str, pd.DataFrame],
    value_kind: str,
) -> list[dict]:
    rows = []
    for year in years:
        route_production = _calculate_route_production_for_region_and_year(product_id, year, tables)
        total_production = sum(route_production.values())
        for route_name, production_t in route_production.items():
            row: dict[str, object] = {
                'scenario': scenario_name,
                'region': region_name,
                'product': PRODUCT_LABELS[product_id],
                'route': route_name,
                'year': f'Y{year}',
            }
            if value_kind == 'production_in_t':
                row[value_kind] = production_t
            else:
                row[value_kind] = (production_t / total_production * 100.0) if total_production > ROUTE_MIN_VALUE else 0.0
            rows.append(row)
    return rows


def _calculate_route_production_for_region_and_year(
    product_id: int, year: int, tables: dict[str, pd.DataFrame]
) -> dict[str, float]:
    context = _TableContext(tables)
    lhv_map = _build_lhv_map(tables.get('energy_carrier_lower_heating_value_in_gj_per_t'), year)
    chain = UpstreamChainBuilder(context, year, lhv_map).trace_upstream(product_id)
    return _classify_chain_into_routes(product_id, chain)


def _classify_chain_into_routes(product_id: int, chain: UpstreamChain) -> dict[str, float]:
    route_definitions = PRODUCT_ROUTE_DEFINITIONS[product_id]
    result = dict.fromkeys(route_definitions, 0.0)
    result[OTHER_ROUTE] = 0.0

    total_output = sum(
        amount for _process_id, final_product_id, amount in chain.final_product_outputs if final_product_id == product_id
    )
    if total_output <= ROUTE_MIN_VALUE:
        return result

    matched_routes = {
        route_name: anchor_ids
        for route_name, anchor_ids in route_definitions.items()
        if anchor_ids and anchor_ids & chain.process_ids
    }
    route_bases = {
        route_name: _route_basis_for_chain(product_id, chain, anchor_ids) for route_name, anchor_ids in matched_routes.items()
    }

    purchase_route_bases = _purchase_route_bases(product_id, chain)
    for route_name, route_basis in purchase_route_bases.items():
        route_bases[route_name] = route_bases.get(route_name, 0.0) + route_basis

    if not route_bases:
        result[OTHER_ROUTE] = total_output
        return result

    total_basis = sum(route_bases.values())
    if total_basis > ROUTE_MIN_VALUE:
        for route_name, route_basis in route_bases.items():
            result[route_name] = total_output * (route_basis / total_basis)
        return result

    if len(route_bases) == 1:
        only_route = next(iter(route_bases))
        result[only_route] = total_output
        return result

    result[OTHER_ROUTE] = total_output
    return result


def _route_basis_for_chain(product_id: int, chain: UpstreamChain, anchor_ids: set[int]) -> float:
    if product_id in {AMMONIA_PRODUCT_ID, METHANOL_PRODUCT_ID}:
        carrier_basis = sum(
            amount for producer_id, _carrier_id, _consumer_id, amount in chain.carrier_flows if producer_id in anchor_ids
        )
        if carrier_basis > ROUTE_MIN_VALUE:
            return carrier_basis

    final_output_basis = sum(
        amount for producer_id, _product_id, amount in chain.final_product_outputs if producer_id in anchor_ids
    )
    if final_output_basis > ROUTE_MIN_VALUE:
        return final_output_basis

    product_basis = sum(
        amount for producer_id, _product_id, _consumer_id, amount in chain.product_flows if producer_id in anchor_ids
    )
    if product_basis > ROUTE_MIN_VALUE:
        return product_basis

    by_product_basis = sum(
        amount for producer_id, _by_product_id, _consumer_id, amount in chain.by_product_flows if producer_id in anchor_ids
    )
    return by_product_basis


def _purchase_route_bases(product_id: int, chain: UpstreamChain) -> dict[str, float]:
    purchase_routes = PURCHASE_ROUTE_DEFINITIONS.get(product_id, {})
    if not purchase_routes:
        return {}

    route_bases = {}
    for route_name, definition in purchase_routes.items():
        carrier_ids = definition['carrier_ids']
        product_ids = definition['product_ids']
        carrier_basis = sum(
            amount for carrier_id, _consumer_id, amount in chain.purchased_carrier_flows if carrier_id in carrier_ids
        )
        product_basis = sum(
            amount for product_id, _consumer_id, amount in chain.purchased_product_flows if product_id in product_ids
        )
        total_basis = carrier_basis + product_basis
        if total_basis > ROUTE_MIN_VALUE:
            route_bases[route_name] = total_basis
    return route_bases


def _read_chain_tables(database_path: str | Path) -> dict[str, pd.DataFrame]:
    database_path = str(database_path)
    connection = sqlite3.connect(database_path)
    try:
        table_names = [*CHAIN_TABLE_NAMES, REGION_TABLE_NAME, SCENARIO_TABLE_NAME]
        return {name: _read_required_table(connection, name, database_path) for name in table_names}
    finally:
        connection.close()


def _read_required_table(connection: sqlite3.Connection, table_name: str, database_path: str) -> pd.DataFrame:
    """Read a table that the export depends on, failing with a clear remedy if it is missing.

    An empty-but-present table is a legitimate result of a simulation that produced no data for
    that table (TabularVisitor always creates its result tables, even when empty); only a missing
    table indicates the simulation has not run, or ran against a different database.
    """
    try:
        return pd.read_sql_query(f'SELECT * FROM `{table_name}`', connection)
    except (sqlite3.OperationalError, pd.errors.DatabaseError) as error:
        message = (
            f"Table '{table_name}' not found in '{database_path}'. "
            'The export runs after the simulation; ensure the simulation completed '
            'and wrote its result tables before exporting product route shares.'
        )
        raise RuntimeError(message) from error


def _region_name_map(region_df: pd.DataFrame | None) -> dict[int, str]:
    if region_df is None or region_df.empty:
        return {}
    return {int(row['id']): str(row['name']) for _, row in region_df.iterrows()}


def _region_ids_for_export(tables: dict[str, pd.DataFrame], scenario_id: int) -> list[int]:
    product_df = tables.get('process_product_production_in_t')
    if product_df is None or product_df.empty or 'id_region' not in product_df.columns:
        return []

    target_product_ids = list(PRODUCT_ROUTE_DEFINITIONS)
    filtered = product_df[product_df['id_product'].isin(target_product_ids)]
    if 'id_scenario' in filtered.columns:
        filtered = filtered[filtered['id_scenario'] == scenario_id]
    if filtered.empty:
        return []

    region_series = filtered['id_region']
    return sorted({int(region_id) for region_id in region_series if not pd.isna(region_id)})


def _filter_tables_for_region(
    tables: dict[str, pd.DataFrame], region_id: int, *, scenario_id: int | None = None
) -> dict[str, pd.DataFrame]:
    filtered_tables = {}
    for table_name, df in tables.items():
        if table_name in {REGION_TABLE_NAME, 'energy_carrier_lower_heating_value_in_gj_per_t'}:
            filtered_tables[table_name] = df
            continue

        if df is None or df.empty:
            filtered_tables[table_name] = df
            continue

        filtered_df = df
        if scenario_id is not None and 'id_scenario' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['id_scenario'] == scenario_id]
        if 'id_region' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['id_region'] == region_id]
        filtered_tables[table_name] = filtered_df.copy()
    return filtered_tables


def _build_lhv_map(lhv_df: pd.DataFrame | None, year: int) -> dict[int, float]:
    if lhv_df is None or lhv_df.empty:
        return {}

    preferred_columns = [f'Y{year}', str(year), 'lower_heating_value_in_gj_per_t', 'value']
    id_column = 'id_energy_carrier' if 'id_energy_carrier' in lhv_df.columns else 'id'
    value_column = next((column for column in preferred_columns if column in lhv_df.columns), None)

    lhv_map = {}
    for _, row in lhv_df.iterrows():
        carrier_id = int(row[id_column])
        value = row[value_column] if value_column is not None else UpstreamChainBuilder.DEFAULT_LHV_GJ_PER_T
        if value is None or pd.isna(float(value)):
            value = UpstreamChainBuilder.DEFAULT_LHV_GJ_PER_T
        lhv_map[carrier_id] = float(value)
    return lhv_map


def _save_wide_table(
    rows: list[dict],
    output_directory: Path,
    table_name: str,
    value_column: str,
    index_columns: list[str],
) -> None:
    df = pd.DataFrame(rows)
    if df.empty:
        empty_data = {column: [] for column in index_columns}
        df = pd.DataFrame(empty_data)
    else:
        df = df.pivot_table(index=index_columns, columns='year', values=value_column).reset_index()
        df.columns.name = None

    excel_path = output_directory / f'{table_name}.xlsx'
    sqlite_path = output_directory / 'output.sqlite'
    connection = sqlite3.connect(sqlite_path)
    try:
        merged_df = _merge_export_table(connection, table_name, df, index_columns)
        merged_df.to_sql(table_name, connection, if_exists='replace', index=False)
        connection.commit()
    finally:
        connection.close()
    merged_df.to_excel(excel_path, index=False)


def _save_iamc_production_table(
    rows: list[dict],
    output_directory: Path,
    table_name: str,
    scenario_name: str,
) -> None:
    iamc_config = IamcExportConfig(model=FORECAST_MODEL_NAME, scenario=scenario_name)
    iamc_long_df = build_iamc_long_table(
        rows,
        config=iamc_config,
        region_mapper=region_name_to_iamc_code,
        variable_mapper=_iamc_variable_name,
        value_mapper=_iamc_production_value,
    )
    iamc_wide_df = pivot_iamc_wide_table(iamc_long_df, variable_column_name=iamc_config.variable_column_name)
    save_iamc_table(iamc_wide_df, output_directory, table_name)


def _iamc_variable_name(row: dict) -> str:
    return f'{row["product"]}|{row["route"]}'


def _iamc_production_value(row: dict) -> tuple[str, float]:
    return 'Mt/year', float(row['production_in_t']) / TONS_PER_MEGATON


def _merge_export_table(
    connection: sqlite3.Connection,
    table_name: str,
    new_df: pd.DataFrame,
    index_columns: list[str],
) -> pd.DataFrame:
    try:
        existing_df = pd.read_sql_query(f'SELECT * FROM `{table_name}`', connection)
    except (sqlite3.OperationalError, pd.errors.DatabaseError):
        return new_df

    if existing_df.empty:
        return new_df
    if new_df.empty:
        return existing_df

    existing_indexed = existing_df.set_index(index_columns)
    new_indexed = new_df.set_index(index_columns)
    kept_existing = existing_indexed.loc[~existing_indexed.index.isin(new_indexed.index)]
    all_columns = kept_existing.columns.union(new_indexed.columns)
    kept_existing = kept_existing.reindex(columns=all_columns)
    new_indexed = new_indexed.reindex(columns=all_columns)
    merged_df = pd.concat([kept_existing, new_indexed]).reset_index()
    return merged_df
