# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from utils import spell_checker


def test_check():
    text = 'This is a simple txt with some erors'
    result = spell_checker.check(text)
    assert result == {
        'txt': 'text',
        'erors': 'errors',
    }
