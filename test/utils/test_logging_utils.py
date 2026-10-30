# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from colorlog import ColoredFormatter

import utils.logging_utils


def test_initialize_logging():
    utils.logging_utils.initialize_logging()
    logger = logging.getLogger()
    handler = logger.handlers[-1]
    formatter = handler.formatter
    assert isinstance(formatter, ColoredFormatter)


def test_debug():
    utils.logging_utils.initialize_logging()
    logging.debug('Demo debug message from test_logging_utils.py')
