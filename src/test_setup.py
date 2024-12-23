# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys

src_path = os.path.dirname(os.path.abspath(__file__))
print('including src directory in python path for testing: ' + src_path)

sys.path.append(src_path)
