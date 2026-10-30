# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from abc import ABC, abstractmethod

from result.visitor.visitor import Visitor


class Entity(ABC):
    def __init__(self, id_entity):
        self._id = id_entity

    @property
    def id(self) -> int:
        return self._id

    def __repr__(self):
        class_name = type(self).__name__
        return f'{class_name}(id={self._id})'

    @abstractmethod
    def accept(self, visitor: Visitor, year):
        # This method belongs to the visitor pattern, also see visitor.visitor.py

        message = 'You should implement this.'
        raise NotImplementedError(message)
