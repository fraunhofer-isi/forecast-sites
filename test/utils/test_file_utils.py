# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.
import pathlib

from test_utils.isi_mock import patch

from utils import file_utils


class TestCreateFolderIfNotExists:
    @patch(pathlib.Path.__init__, None)
    @patch(pathlib.Path.is_dir, True)
    def test_folder_exists(self):
        with patch(pathlib.Path.mkdir) as mocked_mkdir:
            file_utils.create_folder_if_not_exists('folder_path')
            assert not mocked_mkdir.called

    @patch(pathlib.Path.__init__, None)
    @patch(pathlib.Path.is_dir, False)
    def test_folder_does_not_exist(self):
        with patch(pathlib.Path.mkdir) as mocked_mkdir:
            file_utils.create_folder_if_not_exists('folder_path')
            assert mocked_mkdir.called


class TestDeleteFileIfExists:
    @patch(pathlib.Path.__init__, None)
    @patch(pathlib.Path.is_file, True)
    def test_file_exists(self):
        with patch(pathlib.Path.unlink) as mocked_unlink:
            file_utils.delete_file_if_exists('file_path')
            assert mocked_unlink.called

    @patch(pathlib.Path.__init__, None)
    @patch(pathlib.Path.is_file, False)
    def test_does_not_exist(self):
        with patch(pathlib.Path.unlink) as mocked_unlink:
            file_utils.delete_file_if_exists('file_path')
            assert not mocked_unlink.called
