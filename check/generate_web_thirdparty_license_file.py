# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Generate web/THIRDPARTY.md from npm package metadata via generate-license-file.

Runs the npm generate-license-file tool and then prepends a REUSE-compliant header
to the output. This ensures the file is compliant with REUSE Specification 3.3
and avoids unnecessary churn from reuse annotate.

Run:  python check/generate_web_thirdparty_license_file.py
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_WEB_DIR = Path('web')
_OUTPUT = _WEB_DIR / 'THIRDPARTY.md'
_EXIT_INTERNAL_ERROR = 2

# REUSE-IgnoreStart
# This must match byte for byte what `reuse annotate --merge-copyrights -t fraunhofer` produces,
# otherwise every CI run costs two commits: the generation workflow writes one form, the
# reuse_annotate workflow rewrites it into the other, and the next generation undoes that again.
# The net change is zero. Verified as a fixed point by running annotate twice over this file and
# comparing hashes. The template in .reuse/templates/fraunhofer.jinja2 is what adds the AI note;
# that note is free text rather than an SPDX tag, so annotate's defaults cannot maintain it.
_SPDX_HEADER = (
    '<!--\n'
    'SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München\n'
    'SPDX-License-Identifier: AGPL-3.0-or-later\n'
    '\n'
    'AI-assisted code generation was used during development.\n'
    '-->'
)
# REUSE-IgnoreEnd


def main() -> None:
    """Generate web/THIRDPARTY.md with REUSE-compliant header."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    args = _parse_args()
    _generate_with_npm(args.output)
    _prepend_header(args.output)
    logger.info('Wrote REUSE-compliant header to %s', args.output)


def _parse_args() -> argparse.Namespace:
    """Parse optional path overrides (defaults fit the repo layout)."""
    parser = argparse.ArgumentParser(description='Generate web/THIRDPARTY.md via npm generate-license-file.')
    parser.add_argument('--output', type=Path, default=_OUTPUT, help='path to write web/THIRDPARTY.md')
    return parser.parse_args()


def _generate_with_npm(output: Path) -> None:
    """Run npm generate-license-file to create the license file."""
    executable = shutil.which('npx')
    if executable is None:
        logger.error('npx not found; install Node.js and npm')
        sys.exit(_EXIT_INTERNAL_ERROR)
    try:
        subprocess.run(  # noqa: S603 -> hardcoded internal command list, no shell
            [
                executable,
                'generate-license-file',
                '--input',
                'package.json',
                '--output',
                'THIRDPARTY.md',
                '--overwrite',
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(_WEB_DIR),
        )
    except subprocess.CalledProcessError as exc:
        logger.exception('npm generate-license-file failed:\n%s', exc.stderr)
        sys.exit(_EXIT_INTERNAL_ERROR)


def _prepend_header(output: Path) -> None:
    """Prepend REUSE header to the generated file."""
    content = output.read_text(encoding='utf-8')
    output.write_text(f'{_SPDX_HEADER}\n\n{content}', encoding='utf-8')


if __name__ == '__main__':
    main()
