from __future__ import annotations

import importlib as _versioned_importlib

versions = (1, 2)
_versioned_modules = {
    1: _versioned_importlib.import_module('targets.class_dispatch.package_v1'),
    2: _versioned_importlib.import_module('targets.class_dispatch.package_v2'),
}

class Test:
    """Generated multi-version class for Test."""
    __module__ = __name__
    _switch_count = 0
    switch_count = 0
    versions = (1, 2)
    member_names = {1: 'Test', 2: 'Test'}

    # 版ごとの呼び分けは生成時にクラス定義へ展開する。
    # 実行時に関数形状を調べる処理はここには残さない。

    class _V1_Impl(object):
        _version_number = 1

        def display(self, *, _wrapper_self=None) -> str:
            if _wrapper_self is not None:
                self = _wrapper_self
            return 'display-v1'

        def super_log(self, message: str, author: str, *, _wrapper_self=None) -> str:
            if _wrapper_self is not None:
                self = _wrapper_self
            return f'super-v1:{message}:{author}'

        def just_for_test(self, *, _wrapper_self=None) -> str:
            if _wrapper_self is not None:
                self = _wrapper_self
            return 'test-v1'

        def __init__(self):
            pass

    class _V2_Impl(object):
        _version_number = 2

        def display(self, *, _wrapper_self=None) -> str:
            if _wrapper_self is not None:
                self = _wrapper_self
            return 'display-v2'

        def log(self, *, _wrapper_self=None) -> str:
            if _wrapper_self is not None:
                self = _wrapper_self
            return 'log-v2'

        def super_log(self, message: str, *, _wrapper_self=None) -> str:
            if _wrapper_self is not None:
                self = _wrapper_self
            return f'super-v2:{message}'

        def just_for_test(self, *, _wrapper_self=None) -> str:
            if _wrapper_self is not None:
                self = _wrapper_self
            return 'test-v2'

        def __init__(self):
            pass

    _TEST_VERSION_INSTANCES_SINGLETON = [_V1_Impl(), _V2_Impl()]

    def __init__(self, *args, **kwargs):
        self._test_current_state = self._TEST_VERSION_INSTANCES_SINGLETON[0]
        try:
            if args or kwargs:
                raise TypeError('Version 1 of class Test does not define __init__.')
            return
        except (AttributeError, TypeError):
            if not args and not kwargs:
                self._test_switch_to_version(1)
                if args or kwargs:
                    raise TypeError('Version 1 of class Test does not define __init__.')
                return
            if not args and not kwargs:
                self._test_switch_to_version(2)
                if args or kwargs:
                    raise TypeError('Version 2 of class Test does not define __init__.')
                return
            raise TypeError('No version of class Test matches the provided constructor arguments.')

    def _test_switch_to_version(self, version_num):
        type(self)._switch_count += 1
        current_version_num = self._test_current_state._version_number
        self._test_current_state = self._TEST_VERSION_INSTANCES_SINGLETON[version_num - 1]

    @property
    def current_version(self):
        return self._test_current_state._version_number

    @classmethod
    def implementation(cls, version):
        if version == 1:
            return cls._V1_Impl
        if version == 2:
            return cls._V2_Impl
        raise KeyError(f'Unknown version {version!r}')

    for_version = implementation

    def switch_to_version(self, version):
        self._test_switch_to_version(version)


    def display(self):
        try:
            return self._test_current_state.display(_wrapper_self=self)
        except AttributeError:
            self._test_switch_to_version(1)
            return self._test_current_state.display(_wrapper_self=self)

    def just_for_test(self):
        try:
            return self._test_current_state.just_for_test(_wrapper_self=self)
        except AttributeError:
            self._test_switch_to_version(1)
            return self._test_current_state.just_for_test(_wrapper_self=self)

    def log(self):
        try:
            return self._test_current_state.log(_wrapper_self=self)
        except AttributeError:
            self._test_switch_to_version(2)
            return self._test_current_state.log(_wrapper_self=self)

    def super_log(self, *args, **kwargs):
        try:
            return self._test_current_state.super_log(*args, _wrapper_self=self, **kwargs)
        except (AttributeError, TypeError):
            if len(args) <= 2 and kwargs.keys() <= {'message', 'author'} and (len(args) > 0 or 'message' in kwargs) and (len(args) > 1 or 'author' in kwargs) and not (len(args) > 0 and 'message' in kwargs) and not (len(args) > 1 and 'author' in kwargs):
                self._test_switch_to_version(1)
                return self._test_current_state.super_log(*args, _wrapper_self=self, **kwargs)
            elif len(args) <= 1 and kwargs.keys() <= {'message'} and (len(args) > 0 or 'message' in kwargs) and not (len(args) > 0 and 'message' in kwargs):
                self._test_switch_to_version(2)
                return self._test_current_state.super_log(*args, _wrapper_self=self, **kwargs)
            else:
                raise TypeError('No version of method Test.super_log matches the provided arguments.')
