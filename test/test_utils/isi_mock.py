# © 2024 - 2025 Fraunhofer-Gesellschaft e.V., München
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# pylint: disable = import-self
import io
import sys

from mock import MagicMock
from mock import Mock as OriginalMock
from mock import PropertyMock as OriginalPropertyMock
from mock import call as original_call
from mock import mock_open as original_mock_open
from mock import patch as original_patch
from pytest import fixture as original_fixture
from pytest import raises as original_raises


class Mock(MagicMock):
    # This class serves as a wrapper for MagicMock to allow for shorter syntax

    def __new__(cls, *args, **kwargs):
        if len(args) > 0:
            first_argument = args[0]
            mock = MagicMock(return_value=first_argument, *args[1:], **kwargs)
        else:
            mock = MagicMock(**kwargs)
        return mock

    def assert_called_once(self):  # pylint: disable = useless-parent-delegation
        # pylint did not find this method without defining it as a proxy
        super().assert_called_once()

    def assert_called_once_with(  # pylint: disable = useless-parent-delegation, arguments-differ
        self,
        *args,
        **kwargs,
    ):
        # pylint did not find this method without defining it as a proxy
        super().assert_called_once(*args, **kwargs)

    def assert_not_called(self):  # pylint: disable = useless-parent-delegation
        # pylint did not find this method without defining it as a proxy
        super().assert_not_called()


PropertyMock = OriginalPropertyMock


def call(*args, **kwargs):
    return original_call(*args, **kwargs)


def fixture(*args, **kwargs):
    return original_fixture(*args, **kwargs)


def mock_open(*args, **kwargs):
    return original_mock_open(*args, **kwargs)


def patch(item_to_patch, *args, **kwargs):
    if isinstance(item_to_patch, str):
        raise KeyError('Please import and use functions directly instead of passing string paths!')

    module_path = item_to_patch.__module__
    if hasattr(item_to_patch, '__qualname__'):
        item_path = module_path + '.' + item_to_patch.__qualname__
    else:
        name = _try_to_get_object_name(item_to_patch, module_path)
        item_path = module_path + '.' + name

    item_path = item_path.lstrip('_')

    if len(args) == 0 and len(kwargs) == 0:
        return original_patch(item_path, Mock())

    if len(args) == 1 and len(kwargs) == 0:
        result = args[0]
        if not isinstance(result, OriginalMock):
            if not callable(result):
                mock = Mock(result)
                return original_patch(item_path, mock)

    return original_patch(item_path, *args, **kwargs)


def patch_by_string(item_path, return_value):
    return original_patch(item_path, Mock(return_value))


def patch_property(property_to_patch, return_value):
    if isinstance(property_to_patch, str):
        raise KeyError('Please import and use properties directly instead of passing string paths!')

    function_to_patch = property_to_patch.fget
    module_path = function_to_patch.__module__
    item_path = module_path + '.' + function_to_patch.__qualname__

    return original_patch(item_path, return_value=return_value, new_callable=OriginalPropertyMock)


def _try_to_get_object_name(object_to_patch, module_path):
    module = __import__(module_path)
    name = None
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if attribute == object_to_patch:
            if name is None:
                name = attribute_name
            else:
                # object is not unique within its parent but used twice
                message = (
                    'Could not identify item to patch because object is not unique.'
                    + ' Please use a unique string path.'
                )
                raise KeyError(message)
    if name is None:
        raise KeyError('Could not identify object to patch.')
    return name


patch.object = original_patch.object


def patch_sqlite_connect(return_value):
    # pylint: disable = attribute-defined-outside-init
    mocked_cursor = Mock()
    mocked_cursor.execute = Mock()
    mocked_cursor.fetchall = Mock(return_value)

    mocked_connection = Mock()
    mocked_connection.__enter__ = Mock(mocked_connection)
    mocked_connection.cursor = Mock(mocked_cursor)

    def mocked_connect(_path):
        return mocked_connection

    return mocked_connect


def raises(*args, **kwargs):
    return original_raises(*args, **kwargs)


def disable_stdout():
    suppress_text = io.StringIO()
    sys.stdout = suppress_text


def enable_stdout():
    sys.stdout = sys.__stdout__
