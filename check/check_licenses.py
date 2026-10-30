# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Check declared dependencies are license-compatible with this project.

Exit codes:
  0 = all dependencies are license-compatible
  1 = at least one dependency is incompatible
  2 = internal error (e.g., licensecheck bug, config error)
"""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from sys import exit as sysexit

from licensecheck.models.license import License
from licensecheck.models.packageinfo import PackageInfo  # noqa: TC002

logger = logging.getLogger(__name__)

_PYPROJECT = Path('pyproject.toml')
_DEFAULT_PYPI_API = 'https://pypi.org'


@dataclass
class LicenseCheckConfig:
    """License-check settings read from [tool.licensecheck] in pyproject.toml."""

    pypi_api: str
    extras: list[str]
    groups: list[str]
    ignore_packages: list[str]
    fail_packages: list[str]
    ignore_licenses: list[str]
    fail_licenses: list[str]
    only_licenses: list[str]
    skip_dependencies: list[str]


def main() -> None:
    """Run the license check and exit with the appropriate code."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        config = _load_config()
        this_license = _project_license()
        incompatible, packages = _run_check(config, this_license)
        report = _format_report(this_license, packages)
        logger.info(report)
        sysexit(1 if incompatible else 0)
    except Exception:
        logger.exception('License check failed')
        sysexit(2)


def _load_config(pyproject_path: Path = _PYPROJECT) -> LicenseCheckConfig:
    """Read [tool.licensecheck] from pyproject.toml with sensible defaults."""
    with pyproject_path.open('rb') as f:
        data = tomllib.load(f)
    cfg = data.get('tool', {}).get('licensecheck', {})
    return LicenseCheckConfig(
        pypi_api=cfg.get('pypi_api', _DEFAULT_PYPI_API),
        extras=cfg.get('extras', ['dev']),
        groups=cfg.get('groups', []),
        ignore_packages=cfg.get('ignore_packages', []),
        fail_packages=cfg.get('fail_packages', []),
        ignore_licenses=cfg.get('ignore_licenses', []),
        fail_licenses=cfg.get('fail_licenses', []),
        only_licenses=cfg.get('only_licenses', []),
        skip_dependencies=cfg.get('skip_dependencies', []),
    )


def _project_license() -> License:
    """Resolve this project's own license to a License enum."""
    from licensecheck import license_matrix, packageinforesolver  # noqa: PLC0415

    text = packageinforesolver.ProjectMetadata.get_license()
    licenses = license_matrix.licenseType(text)
    return next(iter(licenses)) if licenses else License.UNKNOWN


def _run_check(config: LicenseCheckConfig, this_license: License) -> tuple[bool, set[PackageInfo]]:
    """Invoke licensecheck's checker with project config."""
    from licensecheck import checker, packageinforesolver  # noqa: PLC0415

    manager = packageinforesolver.PackageInfoManager(config.pypi_api)
    return checker.check(
        requirements_paths={'pyproject.toml'},
        groups=set(config.groups),
        extras=set(config.extras),
        this_license=this_license,
        package_info_manager=manager,
        ignore_packages=set(config.ignore_packages),
        fail_packages=set(config.fail_packages),
        ignore_licenses=set(config.ignore_licenses),
        fail_licenses=set(config.fail_licenses),
        only_licenses=set(config.only_licenses),
        skip_dependencies=set(config.skip_dependencies),
    )


def _format_report(this_license: License, packages: set[PackageInfo]) -> str:
    """Build a human-readable report, one line per package."""
    lines = [f'Project License: {this_license}']
    for pkg in sorted(packages, key=lambda p: p.name):
        status = '✔' if pkg.licenseCompat else '✘'
        lines.append(f'{status} {pkg.name}: {pkg.license}')
    return '\n'.join(lines)


if __name__ == '__main__':
    main()
