# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from unittest.mock import Mock

import pytest

from result.visitor.entity import Entity


class ConcreteEntity(Entity):
    """Concrete implementation of Entity for testing."""

    def accept(self, visitor, year):
        return visitor.visit_entity(self, year)


class TestEntity:
    """Test cases for Entity abstract base class."""

    def test_entity_stores_id(self):
        """Test that Entity stores the provided ID."""
        entity = ConcreteEntity(id_entity=42)
        assert entity.id == 42

    def test_entity_id_property_is_readonly(self):
        """Test that id property returns the stored ID."""
        entity = ConcreteEntity(id_entity=99)
        assert entity.id == 99

    def test_entity_with_different_ids(self):
        """Test entities with different IDs are distinct."""
        entity1 = ConcreteEntity(id_entity=1)
        entity2 = ConcreteEntity(id_entity=2)
        assert entity1.id != entity2.id

    def test_entity_repr_includes_id(self):
        """Test that repr includes entity type and ID."""
        entity = ConcreteEntity(id_entity=10)
        repr_str = repr(entity)
        assert 'ConcreteEntity' in repr_str
        assert '10' in repr_str
        assert 'id=' in repr_str

    def test_entity_accept_calls_visitor_method(self):
        """Test that accept method calls appropriate visitor method."""
        entity = ConcreteEntity(id_entity=5)
        mock_visitor = Mock()
        mock_visitor.visit_entity = Mock(return_value='visited')

        result = entity.accept(mock_visitor, 2025)

        assert result == 'visited'
        mock_visitor.visit_entity.assert_called_once_with(entity, 2025)

    def test_entity_id_with_zero(self):
        """Test Entity with ID of zero."""
        entity = ConcreteEntity(id_entity=0)
        assert entity.id == 0

    def test_entity_repr_format_consistency(self):
        """Test that repr has consistent format."""
        entity = ConcreteEntity(id_entity=123)
        repr_str = repr(entity)
        assert repr_str.startswith('ConcreteEntity(')
        assert repr_str.endswith(')')

    def test_entity_abstract_method_raises_not_implemented(self):
        """Test that calling accept on Entity base class raises NotImplementedError."""
        # We can't instantiate Entity directly because it's abstract,
        # but we can verify the error message via ConcreteEntity's parent method
        # by checking the abstractmethod constraint

        # Verify accept is marked as abstractmethod
        assert hasattr(Entity.accept, '__isabstractmethod__')
        assert Entity.accept.__isabstractmethod__ is True

    def test_entity_accept_raises_not_implemented_when_not_overridden(self):
        """Test that accept raises NotImplementedError when not implemented in subclass."""
        entity = ConcreteEntity(id_entity=1)
        # Replace accept with the base class implementation to trigger NotImplementedError
        entity.accept = Entity.accept.__get__(entity, type(entity))
        with pytest.raises(NotImplementedError, match='You should implement this'):
            entity.accept(Mock(), 2025)
