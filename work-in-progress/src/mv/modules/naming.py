from __future__ import annotations

import re
import types
from typing import Any, Mapping


def resolve_logical_name(
    versions: Mapping[Any, types.ModuleType],
    *,
    base_name: str | None = None,
    logical_name: str | None = None,
) -> str:
    """明示名を優先し、省略時は `package_v1` 形式から logical name を推論する。"""

    if base_name is not None and logical_name is not None and base_name != logical_name:
        raise ValueError("base_name and logical_name must match when both are specified")
    return base_name or logical_name or infer_logical_name(versions)


def infer_logical_name(versions: Mapping[Any, types.ModuleType]) -> str:
    """`package_v1` のような module 名から logical name `package` を推論する。"""

    candidates = {
        strip_version_suffix(module.__name__.rsplit(".", 1)[-1])
        for module in versions.values()
    }
    if len(candidates) != 1:
        raise ValueError(
            "Cannot infer a unique logical name from version module names; "
            "specify base_name explicitly"
        )
    return candidates.pop()


def strip_version_suffix(module_name: str) -> str:
    match = re.fullmatch(r"(.+)_v\d+", module_name)
    if not match:
        raise ValueError(
            f"Cannot infer logical name from module name {module_name!r}; "
            "expected a suffix like '_v1'"
        )
    return match.group(1)
