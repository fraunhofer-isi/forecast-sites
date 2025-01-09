# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from pathlib import Path


def create_folder_if_not_exists(folder_path):
    path = Path(folder_path)
    if not path.is_dir():
        path.mkdir()


def delete_file_if_exists(file_path):
    path = Path(file_path)
    if path.is_file():
        path.unlink()
