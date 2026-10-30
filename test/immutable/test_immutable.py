# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pytest

from immutable.immutable import Immutable


class TestImmutable:
    """Test cases for Immutable base class."""

    class SampleImmutable(Immutable):
        """Sample immutable class for testing."""

        def __init__(self, value):
            self.value = value
            super().__init__()

    def test_immutable_allows_attribute_setting_before_initialization(self):
        """Test that attributes can be set before initialization completes."""
        obj = self.SampleImmutable(42)
        assert obj.value == 42

    def test_immutable_prevents_attribute_modification_after_initialization(self):
        """Test that attributes cannot be modified after initialization."""
        obj = self.SampleImmutable(42)
        with pytest.raises(AttributeError) as exc_info:
            obj.value = 100
        assert "Cannot modify immutable attribute 'value'" in str(exc_info.value)

    def test_immutable_prevents_new_attribute_addition_after_initialization(self):
        """Test that new attributes cannot be added after initialization."""
        obj = self.SampleImmutable(42)
        with pytest.raises(AttributeError) as exc_info:
            obj.new_field = 'test'
        assert "Cannot modify immutable attribute 'new_field'" in str(exc_info.value)

    def test_immutable_preserves_original_values(self):
        """Test that original values are preserved and accessible."""
        obj = self.SampleImmutable(99)
        assert obj.value == 99
        assert obj._initialized_immutability is True

    def test_immutable_initialization_flag_is_set(self):
        """Test that _initialized_immutability flag is set after initialization."""
        obj = self.SampleImmutable(1)
        assert hasattr(obj, '_initialized_immutability')
        assert obj._initialized_immutability is True
