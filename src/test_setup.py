# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent
logging.debug('Including src directory in python path for testing: %s', src_path)

sys.path.append(str(src_path))
