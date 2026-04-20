from __future__ import annotations

import types
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .family import ModuleFamily
from .naming import resolve_logical_name
from .program import render_module_family_program


def compile_module_family(
    versions: Mapping[Any, types.ModuleType],
    *,
    base_name: str | None = None,
    logical_name: str | None = None,
    member_map: Mapping[str, Mapping[Any, str] | str] | None = None,
    class_syncs: Mapping[
        str,
        Mapping[tuple[Any, Any], Callable[[Any], None]],
    ]
    | None = None,
    class_attributes: Mapping[str, Mapping[Any, Iterable[str]]] | None = None,
    class_version_selection: str = "continuity",
) -> types.ModuleType:
    """複数版 module object から logical module object を組み立てる。"""

    module_name = resolve_logical_name(
        versions,
        base_name=base_name,
        logical_name=logical_name,
    )
    family = ModuleFamily(
        module_name,
        versions,
        member_map=member_map,
        class_syncs=class_syncs,
        class_attributes=class_attributes,
        class_version_selection=class_version_selection,
    )
    return build_logical_module(family)


def compose_module_family(
    versions: Mapping[Any, types.ModuleType],
    *,
    logical_name: str | None = None,
    base_name: str | None = None,
    member_map: Mapping[str, Mapping[Any, str] | str] | None = None,
    class_syncs: Mapping[
        str,
        Mapping[tuple[Any, Any], Callable[[Any], None]],
    ]
    | None = None,
    class_attributes: Mapping[str, Mapping[Any, Iterable[str]]] | None = None,
    class_version_selection: str = "continuity",
) -> types.ModuleType:
    """互換用 alias。新規コードでは compile_module_family を使う。"""

    return compile_module_family(
        versions,
        base_name=base_name,
        logical_name=logical_name,
        member_map=member_map,
        class_syncs=class_syncs,
        class_attributes=class_attributes,
        class_version_selection=class_version_selection,
    )


def build_logical_module(family: ModuleFamily) -> types.ModuleType:
    """生成 source を module namespace で実行し、plain module object を作る。"""

    module = types.ModuleType(family.logical_name)
    module.__dict__["__package__"] = ""
    module.__dict__["__file__"] = f"<generated {family.logical_name}>"

    source = render_module_family_program(family)
    code = compile(source, f"<logical-module-generated:{family.logical_name}>", "exec")
    exec(code, module.__dict__)
    return module
