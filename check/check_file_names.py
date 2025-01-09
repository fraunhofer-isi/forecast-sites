# © 2024 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# This module checks if all file and folder names follow
# the snake_case naming convention.
# It is included from the pyproject.toml file via init-hook
# of pylint.

import os
import re


def main(directory_to_check="."):
    folders_to_exclude = [
        "LICENSES",
        "web",
        ".git",
        ".idea",
        ".pytest_cache",
        ".vscode",
        "__pycache__",
    ]
    file_names_to_exclude = [
        "Dockerfile",
        "README.md",
        "THIRDPARTY.md",
    ]
    check_folders_and_files_to_be_in_snake_case(
        directory_to_check,
        folders_to_exclude,
        file_names_to_exclude,
    )


def check_folders_and_files_to_be_in_snake_case(
    directory_to_check,
    folders_to_exclude,
    file_names_to_exclude,
):
    for path, sub_folders, files in os.walk(directory_to_check):
        for sub_folder in sub_folders:
            if _is_excluded_folder(sub_folder, folders_to_exclude):
                continue

            check_folders_and_files_to_be_in_snake_case(
                directory_to_check + "/" + sub_folder,
                folders_to_exclude,
                file_names_to_exclude,
            )

        if _is_excluded_folder(path, folders_to_exclude):
            continue

        for name in files:
            if name in file_names_to_exclude:
                continue

            _check_snake_case(path, name)
        break


def _is_excluded_folder(path, folders_to_exclude):
    for folder_to_exclude in folders_to_exclude:  # noqa: SIM110
        if folder_to_exclude in path:
            return True
    return False


def _check_snake_case(path, name):
    if not _is_snake_case(name):
        message = "Directory or file name is not in snake_case:\n" + path + "/" + name
        raise NameError(message)


def _is_snake_case(name):
    items = name.split(".")
    name_without_ending = items[0]
    if name_without_ending == "":
        return True

    _rex = re.compile("_?[a-z0-9]+(?:_+[a-z0-9]+)*")
    is_snake = _rex.fullmatch(name_without_ending)
    return is_snake


if __name__ == "__main__":
    main()
