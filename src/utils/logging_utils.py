# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

import colorlog


def initialize_logging(log_level=logging.INFO):
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            '%(log_color)s%(pathname)s:%(lineno)d:%(message)s',
            log_colors={
                'DEBUG': 'blue',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
        )
    )

    logger = colorlog.getLogger()
    logger.addHandler(handler)
    logger.setLevel(log_level)

    pyogrio_logger = logging.getLogger('pyogrio')
    pyogrio_logger.setLevel(logging.ERROR)  # raised from WARNING to ERROR (suppresses truncation warning)
