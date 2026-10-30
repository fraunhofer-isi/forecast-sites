# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Database reader for Industrial Database CSV generation."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

CSV_ENCODING = 'latin-1'


class DatabaseReader:
    """Load and filter data from Excel and CSV sources."""

    def __init__(self, excel_path: Path, csv_encoding: str = CSV_ENCODING):
        self.excel_path = Path(excel_path)
        self.csv_encoding = csv_encoding

    def load_sites_and_plants(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load sites and plants sheets from Excel."""
        logger.info('Loading data from %s', self.excel_path.name)
        df_sites = pd.read_excel(self.excel_path, sheet_name='Sites')
        df_plants = pd.read_excel(self.excel_path, sheet_name='Plants')
        return df_sites, df_plants

    def filter_sites_for_sector(
        self,
        df_sites: pd.DataFrame,
        df_plants: pd.DataFrame,
        plant_type_ids: list[int],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Filter sites and plants to only those relevant for the sector."""
        sector_plants = df_plants[df_plants['IDPlantType'].isin(plant_type_ids)].copy()
        plant_site_ids = set(sector_plants['IDSite'].dropna().unique().astype(int))
        valid_site_ids = set(df_sites['SiteID'].values) & plant_site_ids

        sites_df = df_sites[df_sites['SiteID'].isin(valid_site_ids)].copy()
        sector_plants = sector_plants[sector_plants['IDSite'].isin(valid_site_ids)]

        logger.info('Found %d sites, %d plants', len(sites_df), len(sector_plants))

        return sites_df, sector_plants

    def load_companies(self, path: Path) -> dict[int, str]:
        """Load existing company ID mappings from CSV."""
        companies = {}
        if path.exists():
            with path.open(encoding=self.csv_encoding) as f:
                for row in csv.DictReader(f):
                    companies[int(row['id'])] = row['name']
        return companies
