from __future__ import annotations

import importlib as _versioned_importlib

versions = (1, 2)
_versioned_modules = {
    1: _versioned_importlib.import_module('targets.class_sync.package_v1'),
    2: _versioned_importlib.import_module('targets.class_sync.package_v2'),
}

import math

class Point:
    """Generated multi-version class for Point."""
    __module__ = __name__
    _switch_count = 0
    switch_count = 0
    versions = (1, 2)
    member_names = {1: 'Point', 2: 'Point'}

    # 版ごとの呼び分けは生成時にクラス定義へ展開する。
    # 実行時に関数形状を調べる処理はここには残さない。

    class _V1_Impl(object):
        _version_number = 1

        def __initialize__(self, x: float, y: float, *, _wrapper_self=None):
            if _wrapper_self is not None:
                self = _wrapper_self
            self.x = x
            self.y = y

        def get_cartesian(self, *, _wrapper_self=None) -> tuple[float, float]:
            if _wrapper_self is not None:
                self = _wrapper_self
            return (self.x, self.y)

        def __init__(self):
            pass

    class _V2_Impl(object):
        _version_number = 2

        def __initialize__(self, r: float, theta: float, *, _wrapper_self=None):
            if _wrapper_self is not None:
                self = _wrapper_self
            self.r = r
            self.theta = theta

        def get_polar(self, *, _wrapper_self=None) -> tuple[float, float]:
            if _wrapper_self is not None:
                self = _wrapper_self
            return (self.r, self.theta)

        def __init__(self):
            pass

    _POINT_VERSION_INSTANCES_SINGLETON = [_V1_Impl(), _V2_Impl()]

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, '_is_switching', False)
        self._point_current_state = self._POINT_VERSION_INSTANCES_SINGLETON[0]
        try:
            return self._point_current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
        except (AttributeError, TypeError):
            if len(args) <= 2 and kwargs.keys() <= {'x', 'y'} and (len(args) > 0 or 'x' in kwargs) and (len(args) > 1 or 'y' in kwargs) and not (len(args) > 0 and 'x' in kwargs) and not (len(args) > 1 and 'y' in kwargs):
                self._point_switch_to_version(1)
                return self._point_current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
            if len(args) <= 2 and kwargs.keys() <= {'r', 'theta'} and (len(args) > 0 or 'r' in kwargs) and (len(args) > 1 or 'theta' in kwargs) and not (len(args) > 0 and 'r' in kwargs) and not (len(args) > 1 and 'theta' in kwargs):
                self._point_switch_to_version(2)
                return self._point_current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
            raise TypeError('No version of class Point matches the provided constructor arguments.')

    def _point_switch_to_version(self, version_num):
        type(self)._switch_count += 1
        current_version_num = self._point_current_state._version_number
        if current_version_num == 1:
            if version_num == 2:
                object.__setattr__(self, '_is_switching', True)
                try:
                    self.sync_point_from_v1_to_v2(self)
                finally:
                    object.__setattr__(self, '_is_switching', False)
        elif current_version_num == 2:
            if version_num == 1:
                object.__setattr__(self, '_is_switching', True)
                try:
                    self.sync_point_from_v2_to_v1(self)
                finally:
                    object.__setattr__(self, '_is_switching', False)
        self._point_current_state = self._POINT_VERSION_INSTANCES_SINGLETON[version_num - 1]

    @staticmethod
    def sync_point_from_v1_to_v2(wrapper_obj):
        wrapper_obj.r = math.sqrt(wrapper_obj.x ** 2 + wrapper_obj.y ** 2)
        wrapper_obj.theta = math.atan2(wrapper_obj.y, wrapper_obj.x)

    @staticmethod
    def sync_point_from_v2_to_v1(wrapper_obj):
        wrapper_obj.x = wrapper_obj.r * math.cos(wrapper_obj.theta)
        wrapper_obj.y = wrapper_obj.r * math.sin(wrapper_obj.theta)

    @property
    def current_version(self):
        return self._point_current_state._version_number

    @classmethod
    def implementation(cls, version):
        if version == 1:
            return cls._V1_Impl
        if version == 2:
            return cls._V2_Impl
        raise KeyError(f'Unknown version {version!r}')

    for_version = implementation

    def switch_to_version(self, version):
        self._point_switch_to_version(version)


    @property
    def x(self):
        try:
            return self._x
        except AttributeError:
            self._point_switch_to_version(1)
            return self._x

    @x.setter
    def x(self, value):
        try:
            self._x
        except AttributeError:
            if not object.__getattribute__(self, '_is_switching'):
                self._point_switch_to_version(1)
        self._x = value

    @property
    def y(self):
        try:
            return self._y
        except AttributeError:
            self._point_switch_to_version(1)
            return self._y

    @y.setter
    def y(self, value):
        try:
            self._y
        except AttributeError:
            if not object.__getattribute__(self, '_is_switching'):
                self._point_switch_to_version(1)
        self._y = value

    @property
    def r(self):
        try:
            return self._r
        except AttributeError:
            self._point_switch_to_version(2)
            return self._r

    @r.setter
    def r(self, value):
        try:
            self._r
        except AttributeError:
            if not object.__getattribute__(self, '_is_switching'):
                self._point_switch_to_version(2)
        self._r = value

    @property
    def theta(self):
        try:
            return self._theta
        except AttributeError:
            self._point_switch_to_version(2)
            return self._theta

    @theta.setter
    def theta(self, value):
        try:
            self._theta
        except AttributeError:
            if not object.__getattribute__(self, '_is_switching'):
                self._point_switch_to_version(2)
        self._theta = value

    def get_cartesian(self):
        try:
            return self._point_current_state.get_cartesian(_wrapper_self=self)
        except AttributeError:
            self._point_switch_to_version(1)
            return self._point_current_state.get_cartesian(_wrapper_self=self)

    def get_polar(self):
        try:
            return self._point_current_state.get_polar(_wrapper_self=self)
        except AttributeError:
            self._point_switch_to_version(2)
            return self._point_current_state.get_polar(_wrapper_self=self)
