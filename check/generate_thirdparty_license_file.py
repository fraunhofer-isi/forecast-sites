# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Generate THIRDPARTY.md from installed package metadata via pip-licenses.

Reads the project's runtime dependencies from pyproject.toml, resolves the
full transitive tree from installed distribution metadata, fetches each
package's license via the pip-licenses CLI, and renders a per-package section
file at THIRDPARTY.md. The tree is computed from installed metadata, so the
output is independent of any stray packages present in the environment.

Run:  python check/generate_thirdparty_license_file.py
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
import tempfile
import tomllib
from importlib.metadata import distributions
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement

logger = logging.getLogger(__name__)

_PYPROJECT = Path('pyproject.toml')
_OUTPUT = Path('THIRDPARTY.md')
_EXIT_INTERNAL_ERROR = 2
_SEPARATOR = '----------------------------------------'
_TAB = 9
_LF = 10
_VT = 11
_FF = 12
_CR = 13
_SPACE = 32
_DEL = 127
_ALLOWED_CONTROL = frozenset({_TAB, _LF, _VT, _FF, _CR})
_SOFT_CONTROL = str.maketrans({_VT: '\n', _FF: '\n'})


def main() -> None:
    """Resolve the project dependency tree and render the license file."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    args = _parse_args()
    roots = _read_runtime_dependencies(args.pyproject)
    tree = _resolve_dependency_tree(roots)
    packages = _fetch_licenses(tree)
    _render(packages, args.output)
    logger.info('Wrote %d packages to %s', len(packages), args.output)


def _parse_args() -> argparse.Namespace:
    """Parse optional path overrides (defaults fit the repo layout)."""
    parser = argparse.ArgumentParser(description='Generate THIRDPARTY.md via pip-licenses.')
    parser.add_argument('--pyproject', type=Path, default=_PYPROJECT, help='path to pyproject.toml')
    parser.add_argument('--output', type=Path, default=_OUTPUT, help='path to write THIRDPARTY.md')
    return parser.parse_args()


def _read_runtime_dependencies(pyproject: Path) -> list[str]:
    """Return normalized names declared in [project.dependencies]."""
    data = tomllib.loads(pyproject.read_text(encoding='utf-8'))
    return [_normalize(Requirement(spec).name) for spec in data['project']['dependencies']]


def _resolve_dependency_tree(roots: list[str]) -> list[str]:
    """
    Expand roots to the full transitive set via installed metadata.

    Returns the canonical distribution names that pip-licenses matches on.
    """
    installed = {_normalize(dist.metadata['Name']): dist for dist in distributions() if dist.metadata.get('Name')}
    seen: set[str] = set(roots)
    queue: list[str] = list(roots)
    while queue:
        dist = installed.get(queue.pop())
        if dist is None:
            continue
        for raw in dist.requires or []:
            req = Requirement(raw)
            if req.marker is not None and not req.marker.evaluate(default_environment()):
                continue
            name = _normalize(req.name)
            if name not in seen:
                seen.add(name)
                queue.append(name)
    return sorted({installed[n].metadata['Name'] for n in seen if n in installed})


def _fetch_licenses(names: list[str]) -> list[dict]:
    """
    Fetch license metadata for the packages via the pip-licenses CLI.

    Writes JSON to a temporary file and parses it; the CLI contract is the
    stable public interface of the tool.
    """
    executable = shutil.which('pip-licenses')
    if executable is None:
        logger.error('pip-licenses not found; install with `pip install .[license]`')
        sys.exit(_EXIT_INTERNAL_ERROR)
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as handle:
        tmp_path = Path(handle.name)
    try:
        subprocess.run(  # noqa: S603 -> hardcoded internal command list, no shell
            [
                executable,
                '-p',
                *names,
                '--with-license-files',
                '--no-license-path',
                '--with-urls',
                '-f',
                'json',
                '--output-file',
                str(tmp_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(tmp_path.read_text(encoding='utf-8'))
    except subprocess.CalledProcessError as exc:
        logger.exception('pip-licenses failed:\n%s', exc.stderr)
        sys.exit(_EXIT_INTERNAL_ERROR)
    finally:
        tmp_path.unlink(missing_ok=True)


def _render(packages: list[dict], output: Path) -> None:
    """Write the header followed by one section per package."""
    sections = [_format_header(), *(_format_section(pkg) for pkg in packages)]
    output.write_text('\n\n'.join(sections) + '\n', encoding='utf-8')


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


def _format_header() -> str:
    """Return the static header for the file (no timestamp, for clean diffs)."""
    return (
        f'{_SPDX_HEADER}\n\n'
        '# Third-party licenses\n\n'
        'This file lists the third-party packages used by forecast-sites together with '
        'their license texts. It is generated by '
        '`check/generate_thirdparty_license_file.py` from installed package metadata.'
    )


def _format_section(pkg: dict) -> str:
    """Format a single package's license section."""
    lines = [_SEPARATOR, '', f'Package: {pkg["Name"]}', f'Version: {pkg["Version"]}', f'License: {pkg["License"]}']
    url = pkg.get('URL') or ''
    if url and url != 'UNKNOWN':
        lines.append(f'URL: {url}')
    lines.extend(['', _join_license_texts(pkg.get('LicenseTexts') or [])])
    return '\n'.join(lines)


def _join_license_texts(texts: list[str]) -> str:
    """Join license texts, dropping binary segments and sanitizing page breaks."""
    cleaned = [_sanitize(text).strip() for text in texts if text and not _is_binary(text)]
    cleaned = [text for text in cleaned if text]
    if not cleaned:
        return '(No license text file found in the installed distribution.)'
    return '\n\n'.join(cleaned)


def _is_binary(text: str) -> bool:
    """Detect hard binary indicators (ESC, NUL, other control chars, DEL) from pip-licenses bytecode."""
    return any((ord(ch) < _SPACE and ord(ch) not in _ALLOWED_CONTROL) or ord(ch) == _DEL for ch in text)


def _sanitize(text: str) -> str:
    """Replace form feed and vertical tab (page breaks) with newlines for clean output."""
    return text.translate(_SOFT_CONTROL)


def _normalize(name: str) -> str:
    """Normalize a distribution name for matching (PEP 503)."""
    return name.strip().lower().replace('_', '-')


if __name__ == '__main__':
    main()
