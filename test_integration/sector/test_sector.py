# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from test_utils.isi_mock import fixture


@fixture
def sut(sector):
    return sector


def test_construction(sut):
    assert sut is not None
