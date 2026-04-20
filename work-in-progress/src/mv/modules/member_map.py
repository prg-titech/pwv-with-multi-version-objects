from __future__ import annotations

import types
from typing import Any, Mapping


RESERVED_LOGICAL_MEMBER_NAMES = {"versions"}


def normalize_member_map(
    versions: Mapping[Any, types.ModuleType],
    member_map: Mapping[str, Mapping[Any, str] | str] | None,
) -> dict[str, dict[Any, str]]:
    """logical member 名から version ごとの実名への対応を作る。"""

    if member_map is None:
        return build_same_name_member_map(versions)

    out: dict[str, dict[Any, str]] = {}
    for logical_name, mapping in member_map.items():
        if isinstance(mapping, str):
            out[logical_name] = {version: mapping for version in versions}
        else:
            out[logical_name] = dict(mapping)
    return out


def build_same_name_member_map(
    versions: Mapping[Any, types.ModuleType],
) -> dict[str, dict[Any, str]]:
    """同じ名前の public member を自動で対応づける。"""

    out: dict[str, dict[Any, str]] = {}
    for version, module in versions.items():
        for name in vars(module):
            if is_public_module_member_name(name):
                out.setdefault(name, {})[version] = name
    return out


def is_public_module_member_name(name: str) -> bool:
    return not name.startswith("_") and name not in RESERVED_LOGICAL_MEMBER_NAMES
