# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class Immutable:
    """
    Inherit from this class to make attributes immutable after initialization.

    Set self._initialized_immutability = True at the end of your __init__ method to lock attributes.
    """

    def __init__(self):
        self._initialized_immutability = True

    def __setattr__(self, key, value):
        if hasattr(self, '_initialized_immutability') and self._initialized_immutability:
            message = f"Cannot modify immutable attribute '{key}'"
            raise AttributeError(message)
        super().__setattr__(key, value)
