# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Data validation for industrial database input generation."""

from __future__ import annotations

import csv
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

CSV_ENCODING = 'latin-1'


class DataValidator:
    """Validate generated data against process definitions."""

    def __init__(self, csv_encoding: str = CSV_ENCODING):
        self.csv_encoding = csv_encoding

    def validate(self, out: Path, sites: list, sub_pus: list, sector_id: int, sector_name: str) -> None:
        """
        Validate that all processes in sub_pus are defined in id_process.csv.

        Logs errors for missing process definitions.
        """
        id_processes = set()
        proc_path = out / 'id_process.csv'
        if proc_path.exists():
            with proc_path.open(encoding=self.csv_encoding) as f:
                for row in csv.DictReader(f):
                    id_processes.add(int(row['id']))

        used = {e['id_process'] for e in sub_pus}
        for p in used:
            if p not in id_processes:
                logger.error('Process %d not in id_process.csv!', p)

        logger.info(
            'Validation done: %d sites, %d sub-PU entries, sector=%d (%s)',
            len(sites),
            len(sub_pus),
            sector_id,
            sector_name,
        )
