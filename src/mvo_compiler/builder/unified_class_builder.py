import ast

from .skeleton_generator import build_skeleton
from .constructor_generator import build_constructor
from .stub_method_generator import build_stub_methods
from .components import build_getattr_setattr_methods, build_sync_components
from ..symbol_table.symbol_table import SymbolTable
from ..util import logger
from ..util.constants import DEFAULT_VERSION_SELECTION_STRATEGY

def build_unified_class(
    class_name: str,
    state_sync_components: tuple,
    symbol_table: SymbolTable,
    incompatibility: dict | None = None,
    version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY,
) -> ast.ClassDef:
    """
    Orchestrates the transformation of versioned classes' ASTs into a single, unified class AST.
    """
    logger.debug_log(f"Building unified class for: {class_name}")

    # --- Generate unified class skeleton ---
    sync_asts = state_sync_components[1] if state_sync_components else []
    new_class_ast = build_skeleton(class_name, symbol_table, sync_asts)

    # --- Generate constructor ---
    constructor_ast = build_constructor(symbol_table, class_name)

    # --- Generate stub methods ---
    stub_methods = build_stub_methods(
        symbol_table,
        class_name,
        version_selection_strategy,
    )

    # --- Build __getattr__ and __setattr__ methods ---
    getattr_setattr_methods = build_getattr_setattr_methods(class_name, incompatibility)

    # --- Build state synchronization components ---
    sync_methods = build_sync_components(class_name, state_sync_components)

    additions: list[ast.AST] = []
    if constructor_ast:
        additions.append(constructor_ast)
    additions.extend(stub_methods)
    additions.extend(getattr_setattr_methods)
    additions.extend(sync_methods)
    new_class_ast.body.extend(additions)

    # --- Return the fully constructed class AST ---
    return new_class_ast
