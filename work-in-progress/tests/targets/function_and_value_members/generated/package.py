from __future__ import annotations

import importlib as _versioned_importlib

versions = (1, 2)
_versioned_modules = {
    1: _versioned_importlib.import_module('targets.function_and_value_members.package_v1'),
    2: _versioned_importlib.import_module('targets.function_and_value_members.package_v2'),
}

_field_current_version = 1

def field(version=None):
    global _field_current_version
    if version is None:
        version = _field_current_version
    _field_current_version = version
    if version == 1:
        return _versioned_modules[1].field
    if version == 2:
        return _versioned_modules[2].field
    raise KeyError('Unknown version for logical member field')
field.versions = (1, 2)
field.member_names = {1: 'field', 2: 'field'}
field.implementation = field
field.for_version = field

def describe(version, *args, **kwargs):
    if version == 1:
        return _versioned_modules[1].describe(*args, **kwargs)
    if version == 2:
        return _versioned_modules[2].describe(*args, **kwargs)
    raise KeyError('Unknown version for logical member describe')
describe.versions = (1, 2)
describe.member_names = {1: 'describe', 2: 'describe'}
describe.implementation = describe
describe.for_version = describe
