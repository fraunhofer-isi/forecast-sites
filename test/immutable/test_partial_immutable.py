# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""Tests for PartialImmutable class."""

import pytest

from immutable.partial_immutable import PartialImmutable


class TestPartialImmutable:
    """Test PartialImmutable base class behavior."""

    class ImmutableExample(PartialImmutable):
        """Test class that inherits from PartialImmutable."""

        def __init__(self, value):
            self.value = value
            super().__init__()

    class MutableExample(PartialImmutable):
        """Test class with mutable field."""

        def __init__(self, value):
            # Mark field as mutable BEFORE calling super().__init__()
            # We need to initialize parent first without immutability
            self._mutable_fields = []
            self._initialized_immutability = False
            self._allow_mutation('value')
            self.value = value
            self._initialized_immutability = True  # Enable immutability after setting

    def test_attribute_immutable_after_init(self):
        """Test that attributes are immutable after initialization."""
        obj = self.ImmutableExample(42)

        with pytest.raises(AttributeError, match='Cannot modify immutable attribute'):
            obj.value = 100

    def test_allowed_mutation_field_is_mutable(self):
        """Test that allowed fields can be mutated after initialization."""
        obj = self.MutableExample(42)

        # Should not raise - value is in mutable_fields
        obj.value = 100
        assert obj.value == 100

    def test_can_set_attributes_during_initialization(self):
        """Test that attributes can be set during __init__ before super().__init__()."""
        obj = self.ImmutableExample(42)

        assert obj.value == 42

    def test_can_add_new_mutable_field_after_init(self):
        """Test that new mutable fields can be added after initialization."""
        obj = self.ImmutableExample(42)

        # First add the field to mutable list
        obj._allow_mutation('new_field')
        # Then set it
        obj.new_field = 'new_value'

        assert obj.new_field == 'new_value'

    def test_cannot_modify_immutable_field_after_init(self):
        """Test that immutable fields cannot be modified after initialization."""
        obj = self.ImmutableExample(42)

        with pytest.raises(AttributeError, match="Cannot modify immutable attribute 'value'"):
            obj.value = 100

    def test_internal_mutable_fields_list_is_mutable(self):
        """Test that _mutable_fields list can be modified."""
        obj = self.ImmutableExample(42)

        # Should be able to add to mutable fields
        assert 'value' not in obj._mutable_fields
        obj._allow_mutation('value')
        assert 'value' in obj._mutable_fields

    def test_adding_duplicate_mutable_field_skipped(self):
        """Test that adding same field twice doesn't duplicate."""
        obj = self.ImmutableExample(42)

        obj._allow_mutation('value')
        initial_count = len(obj._mutable_fields)

        obj._allow_mutation('value')
        # Should not add duplicate
        assert len(obj._mutable_fields) == initial_count

    def test_initialization_flag_prevents_early_mutation_block(self):
        """Test that immutability only applies after _initialized_immutability is set."""
        obj = object.__new__(self.ImmutableExample)
        # Before calling super().__init__(), should be able to set any attribute
        obj.value = 42
        object.__setattr__(obj, '_mutable_fields', [])
        object.__setattr__(obj, '_initialized_immutability', True)

        # Now value should be immutable
        with pytest.raises(AttributeError):
            obj.value = 100
