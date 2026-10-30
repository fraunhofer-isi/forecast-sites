# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.


class SimulationFactory:
    """Helper class to avoid multiple instantiations of the Mesa model."""

    def __init__(self, model_class):
        self._model_class = model_class
        self._instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = self._model_class(*args, **kwargs)
        return self._instance
