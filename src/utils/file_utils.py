# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import pathlib


def create_folder_if_not_exists(folder_path):
    path = pathlib.Path(folder_path)
    if not path.is_dir():
        path.mkdir()


def delete_file_if_exists(file_path):
    path = pathlib.Path(file_path)
    if path.is_file():
        path.unlink()
