from __future__ import annotations

import importlib
import types
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .compile import compile_module_family
from .install import install_logical_module


def load_module_family(
    versions: Mapping[Any, str],
    *,
    base_name: str | None = None,
    member_map: Mapping[str, Mapping[Any, str] | str] | None = None,
    class_syncs: Mapping[
        str,
        Mapping[tuple[Any, Any], Callable[[Any], None]],
    ]
    | None = None,
    class_attributes: Mapping[str, Mapping[Any, Iterable[str]]] | None = None,
    class_version_selection: str = "continuity",
    install: bool = True,
) -> types.ModuleType:
    """module 名を import し、logical module として compile する。

    `install=True` の場合、戻り値はそのまま `import base_name` で取得できる。
    """

    modules = {
        version: importlib.import_module(module_name)
        for version, module_name in versions.items()
    }
    module = compile_module_family(
        modules,
        base_name=base_name,
        member_map=member_map,
        class_syncs=class_syncs,
        class_attributes=class_attributes,
        class_version_selection=class_version_selection,
    )
    if install:
        install_logical_module(module)
    return module
