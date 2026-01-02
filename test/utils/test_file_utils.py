# © 2024-2026 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import patch

from utils import file_utils


def test_create_folder_if_not_exists():
    with patch('os.path.isdir', return_value=False) as patched_isdir, patch('os.mkdir') as patched_mkdir:
        file_utils.create_folder_if_not_exists('folder_path')
        assert patched_isdir.called
        assert patched_mkdir.called


def test_delete_file_if_exists():
    with patch('os.path.isfile', return_value=True) as patched_isfile, patch('os.remove') as patched_remove:
        file_utils.delete_file_if_exists('file_path')
        assert patched_isfile.called
        assert patched_remove.called
