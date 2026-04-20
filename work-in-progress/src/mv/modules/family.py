from __future__ import annotations

import types
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .member_map import normalize_member_map


class ModuleFamily:
    """複数版 module と logical member 対応を保持する compile 入力。"""

    def __init__(
        self,
        logical_name: str,
        versions: Mapping[Any, types.ModuleType],
        *,
        member_map: Mapping[str, Mapping[Any, str] | str] | None = None,
        class_syncs: Mapping[
            str,
            Mapping[tuple[Any, Any], Callable[[Any], None]],
        ]
        | None = None,
        class_attributes: Mapping[str, Mapping[Any, Iterable[str]]] | None = None,
        class_version_selection: str = "continuity",
    ) -> None:
        if not logical_name:
            raise ValueError("logical_name must not be empty")
        if not versions:
            raise ValueError("versions must not be empty")

        self.logical_name = logical_name
        self.modules = dict(versions)
        self.member_map = normalize_member_map(self.modules, member_map)
        self.class_syncs = dict(class_syncs or {})
        self.class_attributes = dict(class_attributes or {})
        self.class_version_selection = class_version_selection

        for version, module in self.modules.items():
            if not isinstance(module, types.ModuleType):
                raise TypeError(
                    f"Version {version!r} for {logical_name!r} must be a module object"
                )

    @property
    def versions(self) -> tuple[Any, ...]:
        try:
            return tuple(sorted(self.modules))
        except TypeError:
            return tuple(self.modules)
