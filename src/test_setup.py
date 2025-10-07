# © 2024, 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent
logging.debug('Including src directory in python path for testing: %s', src_path)

sys.path.append(str(src_path))
