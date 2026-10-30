# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from input.input_mode import InputMode


class TestInputMode:
    """Test cases for InputMode enum."""

    def test_input_mode_has_sqlite_and_csv_values(self):
        """Test that InputMode has expected enum values."""
        assert InputMode.SQLITE.value == 'SQLITE'
        assert InputMode.CSV.value == 'CSV'

    def test_from_string_returns_sqlite(self):
        """Test from_string returns SQLITE for 'SQLITE'."""
        mode = InputMode.from_string('SQLITE')
        assert mode == InputMode.SQLITE

    def test_from_string_returns_csv(self):
        """Test from_string returns CSV for 'CSV'."""
        mode = InputMode.from_string('CSV')
        assert mode == InputMode.CSV

    def test_from_string_raises_error_for_unknown_mode(self):
        """Test from_string raises ValueError for unknown mode."""
        with pytest.raises(ValueError, match='Unknown input mode: UNKNOWN') as exc_info:
            InputMode.from_string('UNKNOWN')
        assert 'Unknown input mode: UNKNOWN' in str(exc_info.value)

    def test_all_enum_values_parseable(self):
        """Test that all enum values can be parsed back."""
        for mode in InputMode:
            parsed = InputMode.from_string(mode.value)
            assert parsed == mode
