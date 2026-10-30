# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class PartialImmutable:
    """
    Inherit from this class to make attributes per default immutable after initialization.

    Call super constructor super().__init__() after setting your class attributes.
    Use allow_mutation(field_name) to allow specific attributes to be mutable.
    """

    def __init__(self):
        self._mutable_fields = []
        self._initialized_immutability = True

    def __setattr__(self, key, value):
        if hasattr(self, '_initialized_immutability') and self._initialized_immutability:
            if key in self._mutable_fields:
                super().__setattr__(key, value)
            else:
                message = f"Cannot modify immutable attribute '{key}'"
                raise AttributeError(message)
        else:
            super().__setattr__(key, value)

    def _allow_mutation(self, field_name):
        if field_name not in self._mutable_fields:
            self._mutable_fields.append(field_name)
