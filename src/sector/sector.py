# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class Sector:
    def __init__(self, id_sector: int, name: str) -> None:
        self._id = id_sector
        self.name = name

    @property
    def id(self) -> int:
        """Sector ID"""
        return self._id

    def __repr__(self) -> str:
        class_name = type(self).__name__
        return f'{class_name}({self.id}, {self.name})'
