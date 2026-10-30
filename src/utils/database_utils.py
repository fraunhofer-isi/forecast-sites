# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging
import shutil
from pathlib import Path


def initialize_output_database(simulation_options):
    """
    Initialize the output database by copying the input database.

    This function:
    1. Creates the output directory if it doesn't exist
    2. Deletes any existing output.sqlite file
    3. Copies the input database to output.sqlite

    This ensures that the output database contains all input tables,
    and result tables can be added to it during simulation.

    Args:
        simulation_options: Dictionary containing 'database_path' and 'output_directory'

    Raises:
        FileNotFoundError: If the input database does not exist
        OSError: If directory creation or file operations fail
        PermissionError: If file operations are not permitted

    """
    logger = logging.getLogger(__name__)
    input_database_path = Path(simulation_options['database_path'])
    output_directory = Path(simulation_options['output_directory'])
    output_database_path = output_directory / 'output.sqlite'

    logger.info('Initializing output database...')
    logger.debug('  Input database: %s', input_database_path)
    logger.debug('  Output database: %s', output_database_path)

    # Check if input database exists
    if not input_database_path.exists():
        message = f'Input database not found: {input_database_path}'
        raise FileNotFoundError(message)

    # Create output directory if it doesn't exist
    output_directory.mkdir(parents=True, exist_ok=True)
    logger.debug('  Output directory created/verified: %s', output_directory)

    # Delete existing output database if present
    if output_database_path.exists():
        output_database_path.unlink()
        logger.debug('  Deleted existing output database')

    # Copy input database to output location
    shutil.copy2(input_database_path, output_database_path)
    logger.debug('  Copied input database to output location')

    logger.info('Output database initialization complete.')
