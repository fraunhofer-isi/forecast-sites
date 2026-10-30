# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Validate referential integrity of CSV input files via SQLite import."""

from __future__ import annotations

import logging
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from input.csv_to_sqlite import csv_to_sqlite

logger = logging.getLogger(__name__)

OUR_TABLES = frozenset(
    {
        'site',
        'production_unit',
        'sub_production_unit',
        'production_unit_product_mapping_in_t',
        'id_site',
        'id_production_unit',
        'id_sub_production_unit',
        'id_company',
        'group',
    }
)


def check(csv_dir: str | Path) -> bool:
    csv_dir = Path(csv_dir)
    tmp_db = csv_dir.parent / f'{csv_dir.name}_integrity_check.sqlite'

    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    logger.setLevel(logging.INFO)

    logger.info('Importing %s ...', csv_dir)
    try:
        csv_to_sqlite(str(csv_dir), str(tmp_db))
    except Exception:
        logger.exception('SQLite import failed')
        return False
    logger.info('SQLite import: OK')

    conn = sqlite3.connect(str(tmp_db))
    conn.execute('PRAGMA foreign_keys = ON')

    violations = conn.execute('PRAGMA foreign_key_check').fetchall()
    ours = [v for v in violations if v[0] in OUR_TABLES]
    others = [v for v in violations if v[0] not in OUR_TABLES]

    ok = True
    if ours:
        logger.error('%d FK violations in site/PU tables:', len(ours))
        for v in ours[:20]:
            logger.error('  table=%s rowid=%s ref=%s fk=%s', *v)
        ok = False
    else:
        logger.info('Site/PU tables: 0 FK violations')

    if others:
        counts = Counter(v[0] for v in others)
        logger.warning('Pre-existing FK issues in other tables: %d total', len(others))
        for t, c in sorted(counts.items()):
            logger.warning('  %s: %d', t, c)

    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for (t,) in tables:
        if t in OUR_TABLES:
            count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            logger.info('  %s: %d rows', t, count)

    conn.close()
    try:
        tmp_db.unlink(missing_ok=True)
    except PermissionError:
        logger.warning('Could not delete temp DB %s', tmp_db)
    return ok


def main():
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description='Check CSV input integrity')
    parser.add_argument('csv_dir', type=str, help='Path to CSV directory')
    args = parser.parse_args()

    success = check(args.csv_dir)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
