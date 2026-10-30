# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

"""
Pytest configuration and fixtures.

Sets up pythonpath for test discovery and common test utilities.
"""

import sys
from pathlib import Path

# Add src and test directories to pythonpath for imports
# __file__ is in test/, so parent.parent is the project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'test'))
