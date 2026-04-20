from __future__ import annotations

import inspect
import types
from typing import Any, Mapping

from .kinds import MemberKind, is_simple_value


class MemberClassifier:
    """module 内の member を、生成方針を決めるために暫定分類する。"""

    def classify(self, member: Any, *, module: types.ModuleType) -> MemberKind:
        owner_module = getattr(member, "__module__", None)

        if inspect.isfunction(member):
            return (
                MemberKind.FUNCTION
                if owner_module == module.__name__
                else MemberKind.EXTERNAL
            )
        if inspect.isclass(member):
            return (
                MemberKind.CLASS
                if owner_module == module.__name__
                else MemberKind.EXTERNAL
            )
        if inspect.isbuiltin(member):
            return MemberKind.EXTERNAL
        if is_simple_value(member):
            return MemberKind.VALUE
        return MemberKind.OBJECT


def classify_logical_member(
    modules: Mapping[Any, types.ModuleType],
    member_names: Mapping[Any, str],
) -> MemberKind:
    """複数版の実体を見て、logical member 全体の生成方針を決める。"""

    classifier = MemberClassifier()
    kinds = set()

    for version, member_name in member_names.items():
        module = modules.get(version)
        if module is None or not hasattr(module, member_name):
            continue
        kinds.add(classifier.classify(getattr(module, member_name), module=module))

    if not kinds:
        raise ValueError(f"Cannot classify logical member with mapping {member_names!r}")
    if len(kinds) == 1:
        return kinds.pop()
    return MemberKind.OBJECT
