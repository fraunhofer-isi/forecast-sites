# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

# pylint: disable = import-self
import functools
import io
import sys

from mock import MagicMock
from mock import Mock as OriginalMock
from mock import PropertyMock as OriginalPropertyMock
from mock import call as original_call
from mock import mock_open as original_mock_open
from mock import patch as original_patch
from pytest import fixture as original_fixture  # noqa: PT013
from pytest import raises as original_raises  # noqa: PT013


class Mock(MagicMock):
    # This class serves as a wrapper for MagicMock to allow for shorter syntax

    def __new__(cls, *args, **kwargs):
        if len(args) > 0:
            first_argument = args[0]
            mock = MagicMock(
                *args[1:],
                **kwargs,
                return_value=first_argument,
            )
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
        super().assert_called_once_with(*args, **kwargs)

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
        message = 'Please import and use functions directly instead of passing string paths!'
        raise KeyError(message)

    item_path = _build_item_path(item_to_patch)
    is_static, is_class = _descriptor_flags(item_to_patch)

    # Scenario 1: advanced usage specifying an explicit 'new' replacement
    if 'new' in kwargs:
        new_replacement = kwargs['new']
        underlying = new_replacement if isinstance(new_replacement, OriginalMock) else None
        kwargs['new'] = _wrap_descriptor(new_replacement, is_static, is_class)
        patcher = original_patch(item_path, *args, **kwargs)
        return _maybe_wrap_context_manager(patcher, underlying, is_static)

    # Scenario 2: no args/kwargs => auto MagicMock
    if not args and not kwargs:
        replacement = Mock()
        patcher = original_patch(item_path, _wrap_descriptor(replacement, is_static, is_class))
        return _maybe_wrap_context_manager(patcher, replacement, is_static)

    # Scenario 3: single positional value => maybe wrap as Mock
    if len(args) == 1 and not kwargs:
        provided = args[0]
        replacement = Mock(provided) if not isinstance(provided, OriginalMock) and not callable(provided) else provided
        underlying = replacement if isinstance(replacement, OriginalMock) else None
        patcher = original_patch(item_path, _wrap_descriptor(replacement, is_static, is_class))
        return _maybe_wrap_context_manager(patcher, underlying, is_static)

    # Fallback: delegate to original patch with arbitrary args/kwargs (no descriptor wrapping unless 'new')
    patcher = original_patch(item_path, *args, **kwargs)
    return _maybe_wrap_context_manager(patcher, None, is_static)


def _wrap_descriptor(replacement_obj, is_static, is_class):
    if is_static:
        return staticmethod(replacement_obj)
    if is_class:
        return classmethod(replacement_obj)
    return replacement_obj


def _maybe_wrap_context_manager(patcher_obj, underlying, is_static):
    if not (is_static and underlying is not None):
        return patcher_obj

    class _StaticMethodPatchWrapper:
        def __init__(self, patcher, target_mock):
            self._patcher = patcher
            self._target_mock = target_mock

        def __enter__(self):
            self._patcher.__enter__()
            return self._target_mock

        def __exit__(self, exc_type, exc, tb):
            return self._patcher.__exit__(exc_type, exc, tb)

        def __call__(self, func):  # decorator usage
            return self._patcher(func)

    return _StaticMethodPatchWrapper(patcher_obj, underlying)


def _build_item_path(item_to_patch):
    module_path = item_to_patch.__module__
    if hasattr(item_to_patch, '__qualname__'):
        item_path = module_path + '.' + item_to_patch.__qualname__
    else:
        name = _try_to_get_object_name(item_to_patch, module_path)
        item_path = module_path + '.' + name
    return item_path.lstrip('_')


def _descriptor_flags(item_to_patch):
    """
    Return (is_staticmethod, is_classmethod).

    Any exception while introspecting results in (False, False) to keep patching robust.
    """
    is_static = False
    is_class = False
    try:
        if hasattr(item_to_patch, '__qualname__') and '.' in item_to_patch.__qualname__:
            class_qualname, _, func_name = item_to_patch.__qualname__.rpartition('.')

            module_path = item_to_patch.__module__
            module_obj = sys.modules.get(module_path)
            if module_obj is None:
                module_obj = __import__(module_path)
            cls_obj = module_obj
            for part in class_qualname.split('.'):
                cls_obj = getattr(cls_obj, part, None)
                if cls_obj is None:
                    break
            if cls_obj is not None and hasattr(cls_obj, '__dict__'):
                raw_descriptor = cls_obj.__dict__.get(func_name)
                if isinstance(raw_descriptor, staticmethod):
                    is_static = True
                elif isinstance(raw_descriptor, classmethod):
                    is_class = True
    except (AttributeError, ImportError, KeyError, TypeError):
        return False, False
    return is_static, is_class


def patch_by_string(item_path, return_value):
    return original_patch(item_path, Mock(return_value))


def patch_property(property_to_patch, return_value, *, inject_arg=False):
    if isinstance(property_to_patch, str):
        message = 'Please import and use properties directly instead of passing string paths!'
        raise KeyError(message)

    function_to_patch = property_to_patch.fget
    module_path = function_to_patch.__module__
    item_path = module_path + '.' + function_to_patch.__qualname__

    # Underlying real patcher (this WOULD normally inject when used as decorator)
    patcher = original_patch(item_path, return_value=return_value, new_callable=OriginalPropertyMock)

    class _PropertyPatchWrapper:
        def __enter__(self):
            return patcher.__enter__()

        def __exit__(self, exc_type, exc, tb):
            return patcher.__exit__(exc_type, exc, tb)

        def __call__(self, func):
            if inject_arg:
                # Legacy style: delegate directly -> injection happens
                return patcher(func)

            @functools.wraps(func)
            def _wrapped(*args, **kwargs):
                with patcher:
                    return func(*args, **kwargs)

            return _wrapped

    return _PropertyPatchWrapper()


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
                message = 'Could not identify item to patch because object is not unique. Please use a unique string path.'

                raise KeyError(message)
    if name is None:
        message = 'Could not identify object to patch.'
        raise KeyError(message)
    return name


patch.object = original_patch.object


def patch_sqlite_connect(return_value=None):
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
    return original_raises(*args, **kwargs)  # noqa: PT010


def disable_stdout():
    suppress_text = io.StringIO()
    sys.stdout = suppress_text


def enable_stdout():
    sys.stdout = sys.__stdout__
