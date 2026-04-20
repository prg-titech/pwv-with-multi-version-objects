from __future__ import annotations

import importlib as _versioned_importlib

versions = (1, 2)
_versioned_modules = {
    1: _versioned_importlib.import_module('targets.renamed_member_mapping.package_v1'),
    2: _versioned_importlib.import_module('targets.renamed_member_mapping.package_v2'),
}

_field_current_version = 1

def field(version=None):
    global _field_current_version
    if version is None:
        version = _field_current_version
    _field_current_version = version
    if version == 1:
        return _versioned_modules[1].field
    raise KeyError('Unknown version for logical member field')
field.versions = (1,)
field.member_names = {1: 'field'}
field.implementation = field
field.for_version = field

_renamed_field_current_version = 2

def renamed_field(version=None):
    global _renamed_field_current_version
    if version is None:
        version = _renamed_field_current_version
    _renamed_field_current_version = version
    if version == 2:
        return _versioned_modules[2].renamed_field
    raise KeyError('Unknown version for logical member renamed_field')
renamed_field.versions = (2,)
renamed_field.member_names = {2: 'renamed_field'}
renamed_field.implementation = renamed_field
renamed_field.for_version = renamed_field

def method(version, *args, **kwargs):
    if version == 1:
        return _versioned_modules[1].method(*args, **kwargs)
    raise KeyError('Unknown version for logical member method')
method.versions = (1,)
method.member_names = {1: 'method'}
method.implementation = method
method.for_version = method

def renamed_method(version, *args, **kwargs):
    if version == 2:
        return _versioned_modules[2].renamed_method(*args, **kwargs)
    raise KeyError('Unknown version for logical member renamed_method')
renamed_method.versions = (2,)
renamed_method.member_names = {2: 'renamed_method'}
renamed_method.implementation = renamed_method
renamed_method.for_version = renamed_method
