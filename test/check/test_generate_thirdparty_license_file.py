# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for license text sanitization in the THIRDPARTY.md generator."""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[2] / 'check' / 'generate_thirdparty_license_file.py'
_spec = importlib.util.spec_from_file_location('_license_gen', _SCRIPT)
_license_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_license_gen)


def test_join_license_texts_keeps_clean_text():
    """Genuine license text passes through unchanged."""
    texts = ['Redistribution and use in source and binary forms...']
    result = _license_gen._join_license_texts(texts)
    assert result == 'Redistribution and use in source and binary forms...'


def test_join_license_texts_skips_segments_with_escape_sequences():
    """Text segments containing ESC control characters (binary/bytecode) are dropped."""
    clean = 'Copyright (c) 2026 Example. All rights reserved.'
    bytecode = 'Package: fake\n' + '\x1b[110;5u' + 'LicensesHandler.finish'
    result = _license_gen._join_license_texts([clean, bytecode])
    assert clean in result
    assert '\x1b' not in result
    assert 'LicensesHandler' not in result


def test_join_license_texts_skips_segments_with_null_bytes():
    """Segments with NUL or other C0 control chars (except tab/newline/cr) are dropped."""
    clean = 'BSD 3-Clause License\n\nCopyright (c) 2026'
    binary = 'license\x00\x01\x02\x03binary garbage'
    result = _license_gen._join_license_texts([binary, clean])
    assert result == clean
    assert '\x00' not in result


def test_join_license_texts_sanitizes_form_feed():
    """Form feed (0x0C, old page breaks) is replaced with a newline, license text kept."""
    with_ff = 'Copyright (c) 2026 Example\fAll rights reserved.'
    result = _license_gen._join_license_texts([with_ff])
    assert result == 'Copyright (c) 2026 Example\nAll rights reserved.'
    assert '\x0c' not in result


def test_join_license_texts_sanitizes_vertical_tab():
    """Vertical tab (0x0B) is replaced with a newline, license text kept."""
    with_vt = 'Copyright (c) 2026\vExample'
    result = _license_gen._join_license_texts([with_vt])
    assert result == 'Copyright (c) 2026\nExample'
    assert '\x0b' not in result


def test_join_license_texts_skips_segments_with_del_byte():
    """Segments with DEL (0x7F) are dropped, not legitimate license text."""
    clean = 'Copyright (c) 2026 Example.'
    with_del = 'text\x7fdel'
    result = _license_gen._join_license_texts([with_del, clean])
    assert result == clean
    assert '\x7f' not in result


def test_join_license_texts_keeps_tab_newline_carriage_return():
    """Legitimate whitespace (tab, newline, carriage return) does not trigger filtering."""
    text = 'Line 1\nLine 2\r\n\tIndented line'
    result = _license_gen._join_license_texts([text])
    assert result == text


def test_join_license_texts_returns_message_when_all_segments_binary():
    """When every segment is binary, the placeholder message is returned."""
    binary_only = ['\x1b[?25h' + 'garbage\x00']
    result = _license_gen._join_license_texts(binary_only)
    assert 'No license text file found' in result


# REUSE-IgnoreStart
_EXPECTED_HEADER = (
    '<!--\n'
    'SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München\n'
    'SPDX-License-Identifier: AGPL-3.0-or-later\n'
    '\n'
    'AI-assisted code generation was used during development.\n'
    '-->'
)


def test_format_header_matches_the_reuse_annotate_output_exactly():
    """
    The header must be byte-identical to what annotate with the project template writes.

    Otherwise every CI run costs two commits with no net change: the generation workflow writes
    one form and the reuse_annotate workflow rewrites it into the other. The template at
    .reuse/templates/fraunhofer.jinja2 supplies the AI-assisted note, which is free text rather
    than an SPDX tag and therefore cannot come from annotate's defaults.
    """
    assert _license_gen._format_header().startswith(_EXPECTED_HEADER)


def test_format_header_emits_spdx_copyright_and_license():
    """The generated header carries the Fraunhofer copyright and AGPL SPDX tags."""
    header = _license_gen._format_header()
    assert 'SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München' in header
    assert 'SPDX-License-Identifier: AGPL-3.0-or-later' in header
    assert 'AI-assisted code generation was used during development.' in header
    assert '# Third-party licenses' in header


def test_format_header_starts_with_spdx_tags():
    """SPDX tags precede the markdown heading so REUSE reads the file as attributed."""
    header = _license_gen._format_header()
    spdx_end = header.index('AI-assisted code generation was used during development.')
    heading_pos = header.index('# Third-party licenses')
    assert spdx_end < heading_pos
# REUSE-IgnoreEnd
