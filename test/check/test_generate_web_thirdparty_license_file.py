# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for the web third-party license file generator."""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / 'check' / 'generate_web_thirdparty_license_file.py'
_SPEC = importlib.util.spec_from_file_location('_web_license_gen', _SCRIPT)
_web_license_gen = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_web_license_gen)


@pytest.mark.parametrize(
    'output',
    [
        Path('web/THIRDPARTY.md'),
        Path('web/custom-license.md'),
    ],
)
def test_generate_with_npm_passes_absolute_output_path(monkeypatch, output):
    """The npm process receives the requested output path, independent of cwd."""
    command = []

    def capture_command(args, **kwargs):
        command.extend(args)

    monkeypatch.setattr(_web_license_gen.shutil, 'which', lambda _: '/usr/bin/npx')
    monkeypatch.setattr(_web_license_gen.subprocess, 'run', capture_command)

    _web_license_gen._generate_with_npm(output)

    assert command[command.index('--output') + 1] == str(output.resolve())
