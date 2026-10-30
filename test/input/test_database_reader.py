# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for DatabaseReader."""

import csv
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from input.database_reader import CSV_ENCODING, DatabaseReader


class TestDatabaseReader:
    """Test cases for DatabaseReader."""

    @pytest.fixture
    def excel_file(self):
        """Create a test Excel file with sample data."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = Path(f.name)

        # Create DataFrames
        sites_df = pd.DataFrame(
            {
                'SiteID': [1, 2, 3],
                'SiteName': ['Site A', 'Site B', 'Site C'],
                'Location': ['City1', 'City2', 'City3'],
            }
        )

        plants_df = pd.DataFrame(
            {
                'PlantID': [101, 102, 103, 104],
                'IDSite': [1, 1, 2, 3],
                'IDPlantType': [1, 2, 1, 3],
                'PlantName': ['Plant 1', 'Plant 2', 'Plant 3', 'Plant 4'],
            }
        )

        # Write to Excel
        with pd.ExcelWriter(excel_path) as writer:
            sites_df.to_excel(writer, sheet_name='Sites', index=False)
            plants_df.to_excel(writer, sheet_name='Plants', index=False)

        yield excel_path

        # Cleanup
        excel_path.unlink(missing_ok=True)

    def test_database_reader_initialization(self, excel_file):
        """Test that DatabaseReader initializes with Excel file path."""
        reader = DatabaseReader(excel_file)
        assert reader.excel_path == excel_file
        assert reader.csv_encoding == CSV_ENCODING

    def test_database_reader_custom_encoding(self, excel_file):
        """Test that DatabaseReader accepts custom encoding."""
        reader = DatabaseReader(excel_file, csv_encoding='utf-8')
        assert reader.csv_encoding == 'utf-8'

    def test_load_sites_and_plants(self, excel_file):
        """Test loading sites and plants from Excel."""
        reader = DatabaseReader(excel_file)
        sites_df, plants_df = reader.load_sites_and_plants()

        assert len(sites_df) == 3
        assert len(plants_df) == 4
        assert 'SiteID' in sites_df.columns
        assert 'IDSite' in plants_df.columns

    def test_filter_sites_for_sector_single_type(self, excel_file):
        """Test filtering sites for a single plant type."""
        reader = DatabaseReader(excel_file)
        sites_df, plants_df = reader.load_sites_and_plants()

        # Filter for plant type 1
        filtered_sites, filtered_plants = reader.filter_sites_for_sector(sites_df, plants_df, [1])

        assert len(filtered_sites) == 2  # Sites 1 and 2 have plant type 1
        assert len(filtered_plants) == 2  # Two plants of type 1

    def test_filter_sites_for_sector_multiple_types(self, excel_file):
        """Test filtering sites for multiple plant types."""
        reader = DatabaseReader(excel_file)
        sites_df, plants_df = reader.load_sites_and_plants()

        # Filter for plant types 1 and 3
        filtered_sites, filtered_plants = reader.filter_sites_for_sector(sites_df, plants_df, [1, 3])

        assert len(filtered_sites) == 3  # All sites have at least one of these types
        assert len(filtered_plants) == 3

    def test_filter_sites_for_sector_no_matching_types(self, excel_file):
        """Test filtering when no plant types match."""
        reader = DatabaseReader(excel_file)
        sites_df, plants_df = reader.load_sites_and_plants()

        # Filter for non-existent plant type
        filtered_sites, filtered_plants = reader.filter_sites_for_sector(sites_df, plants_df, [999])

        assert len(filtered_sites) == 0
        assert len(filtered_plants) == 0

    def test_load_companies_from_csv(self):
        """Test loading company mappings from CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'companies.csv'

            # Create CSV file
            with csv_path.open('w', encoding=CSV_ENCODING, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name'])
                writer.writeheader()
                writer.writerow({'id': '1', 'name': 'Company A'})
                writer.writerow({'id': '2', 'name': 'Company B'})

            with tempfile.NamedTemporaryFile(suffix='.xlsx') as excel_f:
                excel_path = Path(excel_f.name)
                reader = DatabaseReader(excel_path)

                companies = reader.load_companies(csv_path)

                assert len(companies) == 2
                assert companies[1] == 'Company A'
                assert companies[2] == 'Company B'

    def test_load_companies_nonexistent_file(self):
        """Test loading companies when CSV doesn't exist."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx') as excel_f:
            excel_path = Path(excel_f.name)
            reader = DatabaseReader(excel_path)

            nonexistent = Path('/nonexistent/path/companies.csv')
            companies = reader.load_companies(nonexistent)

            assert companies == {}

    def test_load_companies_empty_csv(self):
        """Test loading companies from empty CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'companies.csv'

            # Create empty CSV
            with csv_path.open('w', encoding=CSV_ENCODING, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name'])
                writer.writeheader()

            with tempfile.NamedTemporaryFile(suffix='.xlsx') as excel_f:
                excel_path = Path(excel_f.name)
                reader = DatabaseReader(excel_path)

                companies = reader.load_companies(csv_path)

                assert companies == {}
