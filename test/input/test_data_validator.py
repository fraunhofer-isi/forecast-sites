# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for DataValidator."""

import csv
import tempfile
from pathlib import Path

from input.data_validator import CSV_ENCODING, DataValidator


class TestDataValidator:
    """Test cases for DataValidator."""

    def test_data_validator_initialization(self):
        """Test that DataValidator initializes with default encoding."""
        validator = DataValidator()
        assert validator.csv_encoding == CSV_ENCODING

    def test_data_validator_custom_encoding(self):
        """Test that DataValidator accepts custom encoding."""
        validator = DataValidator(csv_encoding='utf-8')
        assert validator.csv_encoding == 'utf-8'

    def test_validate_with_valid_processes(self):
        """Test validation when all processes exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)

            # Create id_process.csv
            proc_file = out_path / 'id_process.csv'
            with proc_file.open('w', encoding=CSV_ENCODING, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name'])
                writer.writeheader()
                writer.writerow({'id': '1', 'name': 'Process1'})
                writer.writerow({'id': '2', 'name': 'Process2'})

            validator = DataValidator()
            sites = [{'id': 1}, {'id': 2}]
            sub_pus = [{'id_process': 1}, {'id_process': 2}]

            # Should not raise
            validator.validate(out_path, sites, sub_pus, 1, 'TestSector')

    def test_validate_with_missing_processes(self):
        """Test validation when processes are missing (logs error)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)

            # Create id_process.csv with only process 1
            proc_file = out_path / 'id_process.csv'
            with proc_file.open('w', encoding=CSV_ENCODING, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name'])
                writer.writeheader()
                writer.writerow({'id': '1', 'name': 'Process1'})

            validator = DataValidator()
            sites = [{'id': 1}]
            sub_pus = [{'id_process': 1}, {'id_process': 999}]  # 999 doesn't exist

            # Should not raise, but would log error
            validator.validate(out_path, sites, sub_pus, 1, 'TestSector')

    def test_validate_without_id_process_csv(self):
        """Test validation when id_process.csv doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)

            validator = DataValidator()
            sites = [{'id': 1}]
            sub_pus = [{'id_process': 1}]

            # Should not raise
            validator.validate(out_path, sites, sub_pus, 1, 'TestSector')

    def test_validate_with_empty_sub_pus(self):
        """Test validation with no sub-production units."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)

            proc_file = out_path / 'id_process.csv'
            with proc_file.open('w', encoding=CSV_ENCODING, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name'])
                writer.writeheader()

            validator = DataValidator()
            sites = [{'id': 1}]
            sub_pus = []

            # Should not raise
            validator.validate(out_path, sites, sub_pus, 1, 'TestSector')

    def test_validate_with_multiple_sectors(self):
        """Test validation with different sector information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)

            proc_file = out_path / 'id_process.csv'
            with proc_file.open('w', encoding=CSV_ENCODING, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name'])
                writer.writeheader()
                writer.writerow({'id': '10', 'name': 'SectorProcess'})

            validator = DataValidator()
            sites = [{'id': 1}, {'id': 2}, {'id': 3}]
            sub_pus = [{'id_process': 10}]

            # Should not raise
            validator.validate(out_path, sites, sub_pus, 5, 'Steel')
