from __future__ import annotations

import sys
import types


def install_logical_module(module: types.ModuleType) -> types.ModuleType:
    """logical module object を sys.modules に登録する。"""

    sys.modules[module.__name__] = module
    return module
