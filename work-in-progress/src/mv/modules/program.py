from __future__ import annotations

import ast
import importlib.util
import inspect
import sys
import textwrap
import types
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from ..members.classification import classify_logical_member
from ..members.kinds import MemberKind
from .family import ModuleFamily
from .naming import resolve_logical_name


def compile_module_family_program(
    versions: Mapping[Any, types.ModuleType],
    output_path: str | Path,
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
) -> Path:
    """logical module program を Python source として書き出す。"""

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

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_module_family_program(family), encoding="utf-8")
    return path


def load_module_program(path: str | Path, module_name: str | None = None) -> types.ModuleType:
    """書き出した logical module program を file path から import する。"""

    source_path = Path(path)
    name = module_name or source_path.stem
    spec = importlib.util.spec_from_file_location(name, source_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module program from {source_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def render_module_family_program(family: ModuleFamily) -> str:
    """ModuleFamily を import 可能な Python source に変換する。"""

    lines = [
        "from __future__ import annotations",
        "",
        "import importlib as _versioned_importlib",
        "",
    ]
    lines.extend([
        f"versions = {family.versions!r}",
        "_versioned_modules = {",
    ])
    for version, module in family.modules.items():
        lines.append(
            f"    {version!r}: _versioned_importlib.import_module({module.__name__!r}),"
        )
    lines.extend(["}", ""])

    sync_imports = _collect_sync_imports(family.class_syncs)
    for import_line in sync_imports:
        lines.append(import_line)
    if sync_imports:
        lines.append("")

    member_entries: list[tuple[str, Mapping[Any, str], MemberKind]] = []
    class_member_maps: dict[str, Mapping[Any, str]] = {}
    for logical_name, member_names in family.member_map.items():
        kind = classify_logical_member(family.modules, member_names)
        member_entries.append((logical_name, member_names, kind))
        if kind == MemberKind.CLASS:
            class_member_maps[logical_name] = member_names

    for logical_name, member_names, kind in member_entries:
        if kind == MemberKind.CLASS:
            _render_class(
                lines,
                logical_name=logical_name,
                modules=family.modules,
                member_names=member_names,
                class_member_maps=class_member_maps,
                sync_functions=family.class_syncs.get(logical_name),
                attribute_versions=family.class_attributes.get(logical_name),
                version_selection=family.class_version_selection,
            )
            continue

        for public_name, public_member_names in _split_by_public_name(member_names).items():
            if kind in (MemberKind.FUNCTION, MemberKind.EXTERNAL):
                _render_function(lines, public_name, public_member_names)
            else:
                _render_value(lines, public_name, public_member_names)

    return "\n".join(lines).rstrip() + "\n"


def _collect_sync_imports(
    class_syncs: Mapping[str, Mapping[tuple[Any, Any], Callable[[Any], None]]],
) -> tuple[str, ...]:
    import_lines: dict[str, str] = {}
    for sync_map in class_syncs.values():
        for function in sync_map.values():
            module = inspect.getmodule(function)
            if module is None:
                continue
            try:
                source = inspect.getsource(module)
            except (OSError, TypeError):
                continue
            module_ast = ast.parse(source)
            for statement in module_ast.body:
                if isinstance(statement, (ast.Import, ast.ImportFrom)):
                    line = ast.unparse(statement)
                    import_lines[line] = line
    return tuple(import_lines)


def _render_function(
    lines: list[str],
    public_name: str,
    member_names: Mapping[Any, str],
) -> None:
    lines.append(f"def {public_name}(version, *args, **kwargs):")
    for version, member_name in member_names.items():
        lines.append(f"    if version == {version!r}:")
        lines.append(
            f"        return _versioned_modules[{version!r}].{member_name}(*args, **kwargs)"
        )
    lines.append(
        f"    raise KeyError('Unknown version for logical member {public_name}')"
    )
    _render_metadata(lines, public_name, member_names)
    lines.append("")


def _render_value(
    lines: list[str],
    public_name: str,
    member_names: Mapping[Any, str],
) -> None:
    current_version_name = f"_{public_name}_current_version"
    versions = _sorted_versions(member_names)
    lines.append(f"{current_version_name} = {versions[0]!r}")
    lines.append("")
    lines.append(f"def {public_name}(version=None):")
    lines.append(f"    global {current_version_name}")
    lines.append("    if version is None:")
    lines.append(f"        version = {current_version_name}")
    lines.append(f"    {current_version_name} = version")
    for version, member_name in member_names.items():
        lines.append(f"    if version == {version!r}:")
        lines.append(f"        return _versioned_modules[{version!r}].{member_name}")
    lines.append(
        f"    raise KeyError('Unknown version for logical member {public_name}')"
    )
    _render_metadata(lines, public_name, member_names)
    lines.append("")


def _render_class(
    lines: list[str],
    *,
    logical_name: str,
    modules: Mapping[Any, types.ModuleType],
    member_names: Mapping[Any, str],
    class_member_maps: Mapping[str, Mapping[Any, str]],
    sync_functions: Mapping[tuple[Any, Any], Callable[[Any], None]] | None,
    attribute_versions: Mapping[Any, Iterable[str]] | None,
    version_selection: str,
) -> None:
    constructor_specs = _compiled_constructor_specs(modules, member_names)
    method_specs = _compiled_method_specs(modules, member_names)
    current_state_name = _current_state_name(logical_name)
    singleton_name = _version_singleton_name(logical_name)
    switch_method_name = _switch_method_name(logical_name)
    lines.append(
        f"class {logical_name}{_wrapper_base_suffix(logical_name, modules, member_names, class_member_maps)}:"
    )
    lines.append(f"    \"\"\"Generated multi-version class for {logical_name}.\"\"\"")
    lines.append("    __module__ = __name__")
    lines.append("    _switch_count = 0")
    lines.append("    switch_count = 0")
    lines.append(f"    versions = {_sorted_versions(member_names)!r}")
    lines.append(f"    member_names = {dict(member_names)!r}")
    lines.append("")
    lines.append("    # 版ごとの呼び分けは生成時にクラス定義へ展開する。")
    lines.append("    # 実行時に関数形状を調べる処理はここには残さない。")
    lines.append("")
    _render_implementation_classes(
        lines,
        logical_name=logical_name,
        modules=modules,
        member_names=member_names,
        class_member_maps=class_member_maps,
    )
    impl_calls = ", ".join(f"_V{version}_Impl()" for version in member_names)
    lines.append(f"    {singleton_name} = [{impl_calls}]")
    lines.append("")
    _render_constructor(
        lines,
        logical_name,
        constructor_specs,
        current_state_name=current_state_name,
        switch_method_name=switch_method_name,
        singleton_name=singleton_name,
        needs_switching_guard=bool(attribute_versions),
    )
    _render_switch_method(
        lines,
        logical_name=logical_name,
        sync_functions=sync_functions,
        current_state_name=current_state_name,
        singleton_name=singleton_name,
        switch_method_name=switch_method_name,
    )
    _render_common_class_methods(
        lines,
        member_names,
        current_state_name=current_state_name,
        switch_method_name=switch_method_name,
    )
    _render_attribute_properties(
        lines,
        attribute_versions,
        switch_method_name=switch_method_name,
    )
    for method_name, specs in method_specs.items():
        _render_method(
            lines,
            logical_name,
            method_name,
            specs,
            version_selection,
            current_state_name=current_state_name,
            switch_method_name=switch_method_name,
        )
    lines.append("")


def _render_constructor(
    lines: list[str],
    logical_name: str,
    specs: tuple[dict[str, Any], ...],
    *,
    current_state_name: str,
    switch_method_name: str,
    singleton_name: str,
    needs_switching_guard: bool,
) -> None:
    lines.append("    def __init__(self, *args, **kwargs):")
    if needs_switching_guard:
        lines.append("        object.__setattr__(self, '_is_switching', False)")
    lines.append(f"        self.{current_state_name} = self.{singleton_name}[0]")
    lines.append("        try:")
    lines.extend(_indent(_constructor_call_lines(specs[0], current_state_name), "            "))
    lines.append("        except (AttributeError, TypeError):")
    for spec in specs:
        lines.append(f"            if {spec['condition']}:")
        lines.append(f"                self.{switch_method_name}({spec['version']!r})")
        lines.extend(_indent(_constructor_call_lines(spec, current_state_name), "                "))
    lines.append(
        f"            raise TypeError('No version of class {logical_name} matches the provided constructor arguments.')"
    )
    lines.append("")


def _render_switch_method(
    lines: list[str],
    *,
    logical_name: str,
    sync_functions: Mapping[tuple[Any, Any], Callable[[Any], None]] | None,
    current_state_name: str,
    singleton_name: str,
    switch_method_name: str,
) -> None:
    lines.append(f"    def {switch_method_name}(self, version_num):")
    lines.append("        type(self)._switch_count += 1")
    lines.append(f"        current_version_num = self.{current_state_name}._version_number")
    if sync_functions:
        for index, ((from_version, to_version), function) in enumerate(sync_functions.items()):
            prefix = "if" if index == 0 else "elif"
            lines.append(f"        {prefix} current_version_num == {from_version!r}:")
            lines.append(f"            if version_num == {to_version!r}:")
            lines.append("                object.__setattr__(self, '_is_switching', True)")
            lines.append("                try:")
            lines.append(f"                    self.{function.__name__}(self)")
            lines.append("                finally:")
            lines.append("                    object.__setattr__(self, '_is_switching', False)")
    lines.append(f"        self.{current_state_name} = self.{singleton_name}[version_num - 1]")
    lines.append("")

    if sync_functions:
        rendered: set[Callable[[Any], None]] = set()
        for function in sync_functions.values():
            if function in rendered:
                continue
            rendered.add(function)
            lines.append("    @staticmethod")
            for line in _function_source_lines(function):
                lines.append(f"    {line}")
            lines.append("")


def _render_common_class_methods(
    lines: list[str],
    member_names: Mapping[Any, str],
    *,
    current_state_name: str,
    switch_method_name: str,
) -> None:
    lines.append("    @property")
    lines.append("    def current_version(self):")
    lines.append(f"        return self.{current_state_name}._version_number")
    lines.append("")
    lines.append("    @classmethod")
    lines.append("    def implementation(cls, version):")
    for version in member_names:
        lines.append(f"        if version == {version!r}:")
        lines.append(f"            return cls._V{version}_Impl")
    lines.append("        raise KeyError(f'Unknown version {version!r}')")
    lines.append("")
    lines.append("    for_version = implementation")
    lines.append("")
    lines.append("    def switch_to_version(self, version):")
    lines.append(f"        self.{switch_method_name}(version)")
    lines.append("")


def _render_attribute_properties(
    lines: list[str],
    attribute_versions: Mapping[Any, Iterable[str]] | None,
    *,
    switch_method_name: str,
) -> None:
    if not attribute_versions:
        return

    for version, names in attribute_versions.items():
        for name in names:
            storage_name = f"_{name}"
            lines.append("")
            lines.append("    @property")
            lines.append(f"    def {name}(self):")
            lines.append("        try:")
            lines.append(f"            return self.{storage_name}")
            lines.append("        except AttributeError:")
            lines.append(f"            self.{switch_method_name}({version!r})")
            lines.append(f"            return self.{storage_name}")
            lines.append("")
            lines.append(f"    @{name}.setter")
            lines.append(f"    def {name}(self, value):")
            lines.append("        try:")
            lines.append(f"            self.{storage_name}")
            lines.append("        except AttributeError:")
            lines.append("            if not object.__getattribute__(self, '_is_switching'):")
            lines.append(f"                self.{switch_method_name}({version!r})")
            lines.append(f"        self.{storage_name} = value")


def _render_method(
    lines: list[str],
    logical_name: str,
    method_name: str,
    specs: tuple[dict[str, Any], ...],
    version_selection: str,
    *,
    current_state_name: str,
    switch_method_name: str,
) -> None:
    if _has_consistent_signature(specs):
        _render_consistent_method(
            lines,
            logical_name,
            method_name,
            specs,
            version_selection,
            current_state_name=current_state_name,
            switch_method_name=switch_method_name,
        )
        return

    _render_inconsistent_method(
        lines,
        logical_name,
        method_name,
        specs,
        version_selection,
        current_state_name=current_state_name,
        switch_method_name=switch_method_name,
    )


def _render_consistent_method(
    lines: list[str],
    logical_name: str,
    method_name: str,
    specs: tuple[dict[str, Any], ...],
    version_selection: str,
    *,
    current_state_name: str,
    switch_method_name: str,
) -> None:
    first = specs[0]
    public_parameters = first["parameters"]
    lines.append("")
    lines.append(f"    def {method_name}(self{_public_parameter_suffix(public_parameters)}):")
    if version_selection == "latest":
        latest = specs[-1]
        lines.append(f"        self.{switch_method_name}({latest['version']!r})")
    lines.append("        try:")
    lines.extend(
        _indent(_specific_method_call_lines(first, current_state_name), "            ")
    )
    lines.append("        except AttributeError:")
    target = specs[-1] if version_selection == "latest" else specs[0]
    lines.append(f"            self.{switch_method_name}({target['version']!r})")
    lines.extend(
        _indent(_specific_method_call_lines(target, current_state_name), "            ")
    )


def _render_inconsistent_method(
    lines: list[str],
    logical_name: str,
    method_name: str,
    specs: tuple[dict[str, Any], ...],
    version_selection: str,
    *,
    current_state_name: str,
    switch_method_name: str,
) -> None:
    lines.append("")
    lines.append(f"    def {method_name}(self, *args, **kwargs):")
    if version_selection == "latest":
        latest = specs[-1]
        lines.append(f"        self.{switch_method_name}({latest['version']!r})")
    lines.append("        try:")
    lines.extend(_indent(_method_call_lines(specs[0], current_state_name), "            "))
    lines.append("        except (AttributeError, TypeError):")
    for index, spec in enumerate(specs):
        prefix = "if" if index == 0 else "elif"
        lines.append(f"            {prefix} {spec['condition']}:")
        lines.append(f"                self.{switch_method_name}({spec['version']!r})")
        lines.extend(_indent(_method_call_lines(spec, current_state_name), "                "))
    lines.append("            else:")
    lines.append(
        f"                raise TypeError('No version of method {logical_name}.{method_name} matches the provided arguments.')"
    )


def _render_implementation_classes(
    lines: list[str],
    *,
    logical_name: str,
    modules: Mapping[Any, types.ModuleType],
    member_names: Mapping[Any, str],
    class_member_maps: Mapping[str, Mapping[Any, str]],
) -> None:
    for version, class_name in member_names.items():
        class_object = getattr(modules[version], class_name)
        base_suffix = _implementation_base_suffix(
            logical_name,
            version,
            class_object,
            modules,
            class_member_maps,
        )
        lines.append(f"    class _V{version}_Impl{base_suffix}:")
        lines.append(f"        _version_number = {version!r}")
        lines.append("")

        method_nodes = _implementation_method_nodes(
            logical_name,
            version,
            class_object,
            modules,
            class_member_maps,
        )
        if not method_nodes:
            lines.append("        pass")
            lines.append("")
            continue

        for index, method_node in enumerate(method_nodes):
            if index:
                lines.append("")
            for line in ast.unparse(method_node).splitlines():
                lines.append(f"        {line}")
        lines.append("")
        lines.append("        def __init__(self):")
        lines.append("            pass")
        lines.append("")


def _render_metadata(
    lines: list[str],
    public_name: str,
    member_names: Mapping[Any, str],
) -> None:
    lines.append(f"{public_name}.versions = {_sorted_versions(member_names)!r}")
    lines.append(f"{public_name}.member_names = {dict(member_names)!r}")
    lines.append(f"{public_name}.implementation = {public_name}")
    lines.append(f"{public_name}.for_version = {public_name}")


def _version_singleton_name(class_name: str) -> str:
    return f"_{class_name.upper()}_VERSION_INSTANCES_SINGLETON"


def _current_state_name(class_name: str) -> str:
    return f"_{class_name.lower()}_current_state"


def _switch_method_name(class_name: str) -> str:
    return f"_{class_name.lower()}_switch_to_version"


def _compiled_constructor_specs(
    modules: Mapping[Any, types.ModuleType],
    member_names: Mapping[Any, str],
) -> tuple[dict[str, Any], ...]:
    specs: list[dict[str, Any]] = []
    for version, class_name in member_names.items():
        class_object = getattr(modules[version], class_name)
        constructor = class_object.__dict__.get("__init__")
        specs.append(
            {
                "version": version,
                "class_name": class_name,
                "has_constructor": constructor is not None,
                "condition": _call_signature_condition(
                    constructor,
                    skip_first_parameter=True,
                    requires_no_arguments=constructor is None,
                ),
            }
        )
    return tuple(specs)


def _compiled_method_specs(
    modules: Mapping[Any, types.ModuleType],
    member_names: Mapping[Any, str],
) -> dict[str, tuple[dict[str, Any], ...]]:
    specs_by_name: dict[str, list[dict[str, Any]]] = {}
    for version, class_name in member_names.items():
        class_object = getattr(modules[version], class_name)
        for name, descriptor in vars(class_object).items():
            if name == "__init__" or name.startswith("_"):
                continue
            member = _describe_class_member(class_object, name)
            if member is None:
                continue
            callable_object, receiver = member
            specs_by_name.setdefault(name, []).append(
                {
                    "version": version,
                    "class_name": class_name,
                    "method_name": name,
                    "receiver": receiver,
                    "parameters": _call_parameters(
                        callable_object,
                        skip_first_parameter=receiver != "none",
                    ),
                    "condition": _call_signature_condition(
                        callable_object,
                        skip_first_parameter=receiver != "none",
                    ),
                }
            )
    return {
        name: tuple(specs)
        for name, specs in sorted(specs_by_name.items())
    }


def _describe_class_member(
    class_object: type,
    name: str,
) -> tuple[Callable[..., Any], str] | None:
    descriptor = inspect.getattr_static(class_object, name)
    if isinstance(descriptor, staticmethod):
        return descriptor.__func__, "none"
    if isinstance(descriptor, classmethod):
        return descriptor.__func__, "class"
    if callable(descriptor):
        return descriptor, "instance"
    return None


def _implementation_method_nodes(
    logical_name: str,
    version: Any,
    class_object: type,
    modules: Mapping[Any, types.ModuleType],
    class_member_maps: Mapping[str, Mapping[Any, str]],
) -> list[ast.FunctionDef]:
    class_node = _class_source_node(class_object)
    method_nodes: list[ast.FunctionDef] = []
    parent_context = _parent_context(
        logical_name,
        version,
        class_object,
        modules,
        class_member_maps,
    )
    for statement in class_node.body:
        if not isinstance(statement, ast.FunctionDef):
            continue
        method_node = statement
        if method_node.name == "__init__":
            method_node.name = "__initialize__"
        if _is_staticmethod(method_node) or _is_classmethod(method_node):
            method_nodes.append(method_node)
            continue
        method_nodes.append(
            _WrapperSelfTransformer(logical_name, parent_context).visit(method_node)
        )
    return method_nodes


def _class_source_node(class_object: type) -> ast.ClassDef:
    source = textwrap.dedent(inspect.getsource(class_object))
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            return node
    raise TypeError(f"Cannot find class source for {class_object!r}")


def _function_source_lines(function: Callable[..., Any]) -> list[str]:
    source = textwrap.dedent(inspect.getsource(function))
    node = ast.parse(source).body[0]
    if not isinstance(node, ast.FunctionDef):
        raise TypeError(f"Cannot render sync function source for {function!r}")
    return ast.unparse(node).splitlines()


def _is_staticmethod(method_node: ast.FunctionDef) -> bool:
    return _has_decorator(method_node, "staticmethod")


def _is_classmethod(method_node: ast.FunctionDef) -> bool:
    return _has_decorator(method_node, "classmethod")


def _has_decorator(method_node: ast.FunctionDef, name: str) -> bool:
    return any(
        isinstance(decorator, ast.Name) and decorator.id == name
        for decorator in method_node.decorator_list
    )


def _wrapper_base_suffix(
    logical_name: str,
    modules: Mapping[Any, types.ModuleType],
    member_names: Mapping[Any, str],
    class_member_maps: Mapping[str, Mapping[Any, str]],
) -> str:
    base_exprs: dict[str, str] = {}
    for version, class_name in member_names.items():
        class_object = getattr(modules[version], class_name)
        for base in class_object.__bases__:
            expr = _base_expression(
                base,
                version,
                modules,
                class_member_maps,
                current_logical_name=logical_name,
                prefer_versioned=True,
            )
            if expr is not None:
                base_exprs[expr] = expr
    if not base_exprs:
        return ""
    return "(" + ", ".join(base_exprs) + ")"


def _implementation_base_suffix(
    logical_name: str,
    version: Any,
    class_object: type,
    modules: Mapping[Any, types.ModuleType],
    class_member_maps: Mapping[str, Mapping[Any, str]],
) -> str:
    base_exprs: list[str] = []
    for base in class_object.__bases__:
        expr = _base_expression(
            base,
            version,
            modules,
            class_member_maps,
            current_logical_name=logical_name,
            prefer_versioned=True,
        )
        if expr is not None:
            base_exprs.append(expr)
    if not base_exprs:
        return "(object)"
    return "(" + ", ".join(base_exprs) + ")"


def _parent_context(
    logical_name: str,
    version: Any,
    class_object: type,
    modules: Mapping[Any, types.ModuleType],
    class_member_maps: Mapping[str, Mapping[Any, str]],
) -> tuple[str, str | None] | None:
    for base in class_object.__bases__:
        if base is object:
            continue
        logical_base = _find_logical_class_for_base(
            base,
            version,
            modules,
            class_member_maps,
            current_logical_name=logical_name,
        )
        if logical_base is not None:
            return ("versioned", f"{logical_base}._V{version}_Impl")
        return ("normal", None)
    return None


def _base_expression(
    base: type,
    version: Any,
    modules: Mapping[Any, types.ModuleType],
    class_member_maps: Mapping[str, Mapping[Any, str]],
    *,
    current_logical_name: str,
    prefer_versioned: bool,
) -> str | None:
    if base is object:
        return None
    if prefer_versioned:
        logical_base = _find_logical_class_for_base(
            base,
            version,
            modules,
            class_member_maps,
            current_logical_name=current_logical_name,
        )
        if logical_base is not None:
            return f"{logical_base}._V{version}_Impl"
    return f"_versioned_importlib.import_module({base.__module__!r}).{base.__qualname__}"


def _find_logical_class_for_base(
    base: type,
    version: Any,
    modules: Mapping[Any, types.ModuleType],
    class_member_maps: Mapping[str, Mapping[Any, str]],
    *,
    current_logical_name: str,
) -> str | None:
    for logical_name, member_names in class_member_maps.items():
        if logical_name == current_logical_name:
            continue
        class_name = member_names.get(version)
        if class_name is None:
            continue
        module = modules.get(version)
        if module is None:
            continue
        if getattr(module, class_name, None) is base:
            return logical_name
    return None


class _WrapperSelfTransformer(ast.NodeTransformer):
    """version 実装メソッドを wrapper instance 上で実行する形に変換する。"""

    def __init__(
        self,
        logical_name: str,
        parent_context: tuple[str, str | None] | None,
    ) -> None:
        self.logical_name = logical_name
        self.parent_context = parent_context
        self.in_top_level_method = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if self.in_top_level_method:
            return node
        if not node.args.args:
            return node

        self.in_top_level_method = True

        wrapper_arg = ast.arg(arg="_wrapper_self")
        node.args.kwonlyargs.append(wrapper_arg)
        node.args.kw_defaults.append(ast.Constant(value=None))

        self_name = node.args.args[0].arg
        rebind = ast.If(
            test=ast.Compare(
                left=ast.Name(id="_wrapper_self", ctx=ast.Load()),
                ops=[ast.IsNot()],
                comparators=[ast.Constant(value=None)],
            ),
            body=[
                ast.Assign(
                    targets=[ast.Name(id=self_name, ctx=ast.Store())],
                    value=ast.Name(id="_wrapper_self", ctx=ast.Load()),
                )
            ],
            orelse=[],
        )
        node.body = [rebind, *(self.visit(statement) for statement in node.body)]
        self.in_top_level_method = False
        return ast.fix_missing_locations(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        return node

    def visit_Call(self, node: ast.Call) -> ast.Call:
        if (
            self.in_top_level_method
            and isinstance(node.func, ast.Name)
            and node.func.id == "super"
            and not node.args
            and self.parent_context is not None
        ):
            parent_type, parent_impl_expr = self.parent_context
            if parent_type == "versioned" and parent_impl_expr is not None:
                node.args = [
                    ast.parse(parent_impl_expr, mode="eval").body,
                    ast.Name(id="_wrapper_self", ctx=ast.Load()),
                ]
            elif parent_type == "normal":
                node.args = [
                    ast.Name(id=self.logical_name, ctx=ast.Load()),
                    ast.Name(id="_wrapper_self", ctx=ast.Load()),
                ]
            return node
        return self.generic_visit(node)


def _constructor_call_lines(
    spec: Mapping[str, Any],
    current_state_name: str,
) -> list[str]:
    if not spec["has_constructor"]:
        return [
            "if args or kwargs:",
            f"    raise TypeError('Version {spec['version']!r} of class {spec['class_name']} does not define __init__.')",
            "return",
        ]
    return [
        f"return self.{current_state_name}.__initialize__(*args, _wrapper_self=self, **kwargs)"
    ]


def _method_call_lines(spec: Mapping[str, Any], current_state_name: str) -> list[str]:
    prefix = f"self.{current_state_name}.{spec['method_name']}"
    if spec["receiver"] == "instance":
        return [f"return {prefix}(*args, _wrapper_self=self, **kwargs)"]
    return [f"return {prefix}(*args, **kwargs)"]


def _specific_method_call_lines(
    spec: Mapping[str, Any],
    current_state_name: str,
) -> list[str]:
    prefix = f"self.{current_state_name}.{spec['method_name']}"
    return [f"return {prefix}({_call_arguments(spec['parameters'])})"]


def _has_consistent_signature(specs: tuple[dict[str, Any], ...]) -> bool:
    if not specs:
        return False
    first = _signature_key(specs[0]["parameters"])
    return all(_signature_key(spec["parameters"]) == first for spec in specs[1:])


def _signature_key(parameters: tuple[inspect.Parameter, ...]) -> tuple[str, ...]:
    return tuple(str(parameter) for parameter in parameters)


def _public_parameter_suffix(parameters: tuple[inspect.Parameter, ...]) -> str:
    if not parameters:
        return ""
    return ", " + _signature_text(parameters)


def _signature_text(parameters: tuple[inspect.Parameter, ...]) -> str:
    return str(inspect.Signature(parameters))[1:-1]


def _call_arguments(parameters: tuple[inspect.Parameter, ...]) -> str:
    arguments: list[str] = []
    inserted_wrapper_self = False
    for parameter in parameters:
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            arguments.append(parameter.name)
        elif parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            arguments.append(f"*{parameter.name}")
        elif parameter.kind == inspect.Parameter.KEYWORD_ONLY:
            if not inserted_wrapper_self:
                arguments.append("_wrapper_self=self")
                inserted_wrapper_self = True
            arguments.append(f"{parameter.name}={parameter.name}")
        elif parameter.kind == inspect.Parameter.VAR_KEYWORD:
            if not inserted_wrapper_self:
                arguments.append("_wrapper_self=self")
                inserted_wrapper_self = True
            arguments.append(f"**{parameter.name}")

    if not inserted_wrapper_self:
        arguments.append("_wrapper_self=self")
    return ", ".join(arguments)


def _call_parameters(
    callable_object: Callable[..., Any],
    *,
    skip_first_parameter: bool,
) -> tuple[inspect.Parameter, ...]:
    try:
        signature = inspect.signature(callable_object)
    except (TypeError, ValueError):
        return ()
    parameters = tuple(signature.parameters.values())
    if skip_first_parameter and parameters:
        return parameters[1:]
    return parameters


def _call_signature_condition(
    callable_object: Callable[..., Any] | None,
    *,
    skip_first_parameter: bool,
    requires_no_arguments: bool = False,
) -> str:
    if requires_no_arguments:
        return "not args and not kwargs"
    if callable_object is None:
        return "True"

    try:
        signature = inspect.signature(callable_object)
    except (TypeError, ValueError):
        return "True"

    parameters = list(signature.parameters.values())
    if skip_first_parameter and parameters:
        parameters = parameters[1:]
    return _signature_condition_from_parameters(parameters)


def _signature_condition_from_parameters(parameters: list[inspect.Parameter]) -> str:
    positional: list[inspect.Parameter] = []
    keyword_names: list[str] = []
    required: list[tuple[int | None, str, str]] = []
    has_varargs = False
    has_varkw = False

    for parameter in parameters:
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            has_varargs = True
            continue
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            has_varkw = True
            continue

        positional_index: int | None = None
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional_index = len(positional)
            positional.append(parameter)

        if parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            keyword_names.append(parameter.name)

        if parameter.default is inspect.Parameter.empty:
            required.append((positional_index, parameter.name, parameter.kind.name))

    conditions: list[str] = []
    if not has_varargs:
        conditions.append(f"len(args) <= {len(positional)}")
    if not has_varkw:
        conditions.append(f"kwargs.keys() <= {_set_literal(keyword_names)}")

    for index, name, kind_name in required:
        if kind_name == inspect.Parameter.POSITIONAL_ONLY.name:
            conditions.append(f"len(args) > {index}")
        elif index is None:
            conditions.append(f"{name!r} in kwargs")
        else:
            conditions.append(f"(len(args) > {index} or {name!r} in kwargs)")

    for index, parameter in enumerate(positional):
        if parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            conditions.append(
                f"not (len(args) > {index} and {parameter.name!r} in kwargs)"
            )

    if not conditions:
        return "True"
    return " and ".join(conditions)


def _set_literal(values: Iterable[str]) -> str:
    items = tuple(values)
    if not items:
        return "set()"
    return "{" + ", ".join(repr(item) for item in items) + "}"


def _indent(lines: Iterable[str], prefix: str) -> list[str]:
    return [f"{prefix}{line}" if line else "" for line in lines]


def _split_by_public_name(
    member_names: Mapping[Any, str],
) -> dict[str, dict[Any, str]]:
    out: dict[str, dict[Any, str]] = {}
    for version, public_name in member_names.items():
        out.setdefault(public_name, {})[version] = public_name
    return out


def _sorted_versions(member_names: Mapping[Any, str]) -> tuple[Any, ...]:
    try:
        return tuple(sorted(member_names))
    except TypeError:
        return tuple(member_names)
