# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from abc import ABC, abstractmethod

from visitor.visitor import Visitor


class Entity(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor, year):
        # This method belongs to the visitor pattern, also see visitor.visitor.py

        message = 'You should implement this.'
        raise NotImplementedError(message)
