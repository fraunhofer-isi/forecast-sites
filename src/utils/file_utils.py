# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os


def create_folder_if_not_exists(folder_path):
    if not os.path.isdir(folder_path):
        os.mkdir(folder_path)


def delete_file_if_exists(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
