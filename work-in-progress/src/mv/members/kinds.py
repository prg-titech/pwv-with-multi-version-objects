from __future__ import annotations

from enum import Enum
from typing import Any


class MemberKind(str, Enum):
    """module-level member の暫定分類。分類は生成コードの形を選ぶために使う。"""

    FUNCTION = "function"
    CLASS = "class"
    VALUE = "value"
    OBJECT = "object"
    EXTERNAL = "external"


def is_simple_value(member: Any) -> bool:
    """selector function で扱えば足りる単純な値を判定する。"""

    return isinstance(
        member,
        (str, bytes, int, float, complex, bool, tuple, list, dict, set),
    )
