# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from processes.abstract_process import AbstractProcess


class ProcessOption:
    """Wraps a Process or InstalledProcess and serves as unique key"""

    def __init__(self, process: AbstractProcess):
        self.process: AbstractProcess = process

    def __repr__(self):
        return f'ProcessOption(process={self.process})'
