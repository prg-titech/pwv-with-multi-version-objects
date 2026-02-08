import ast, re, copy

from .skeleton_generator import build_skeleton
from .constructor_generator import build_constructor
from .stub_method_generator import build_stub_methods
from ..symbol_table.symbol_table import SymbolTable
from ..util.template_util import get_template_string
from ..util.ast_util import get_switch_to_version_method_name
from ..util import logger
from ..util.constants import DEFAULT_VERSION_SELECTION_STRATEGY

def build_unified_class(
    class_name: str,
    state_sync_components: tuple,
    symbol_table: SymbolTable,
    incompatibility: dict | None = None,
    version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY,
) -> ast.Module:
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

    # --- Inject __getattr__ and __setattr__ methods ---
    getattr_setattr_methods = build_getattr_setattr_methods(class_name, incompatibility)

    # --- Inject state synchronization components ---
    sync_methods = build_sync_components(class_name, state_sync_components)

    additions: list[ast.AST] = []
    if constructor_ast:
        additions.append(constructor_ast)
    additions.extend(stub_methods)
    additions.extend(getattr_setattr_methods)
    additions.extend(sync_methods)
    new_class_ast.body.extend(additions)

    # --- Return the fully constructed class AST ---
    return ast.Module(body=[new_class_ast], type_ignores=[])

def build_sync_components(
    class_name: str,
    state_sync_components: tuple | None,
) -> list[ast.FunctionDef]:
    """
    Builds sync functions from the sync module as static methods.
    """
    if not state_sync_components:
        return []

    _, sync_functions = state_sync_components
    logger.debug_log(f"Injecting {len(sync_functions)} sync functions for {class_name}")

    out: list[ast.FunctionDef] = []
    for func_node in sync_functions:
        func_copy = copy.deepcopy(func_node)
        func_copy.decorator_list.append(ast.Name(id='staticmethod', ctx=ast.Load()))
        out.append(func_copy)

    return out

# Preliminary
def build_getattr_setattr_methods(
    class_name: str,
    incompatibility: dict | None = None,
) -> list[ast.FunctionDef]:
    """
    Builds __getattr__ and __setattr__ methods to handle dynamic attribute access.
    """
    if incompatibility is None:
        return []

    getter_template_string = get_template_string("getter_template.py")
    setter_template_string = get_template_string("setter_template.py")
    switch_method_name = get_switch_to_version_method_name(class_name)

    out: list[ast.FunctionDef] = []
    for version, attr_list in incompatibility.items():
        for attr in attr_list:
            logger.debug_log(
                f"Injecting __getattr__ and __setattr__ for attribute '{attr}' in version {version}"
            )
            getter_template_copy = re.sub(r'\[ATTR\]', attr, getter_template_string)
            getter_template_copy = re.sub(r'\[VERSION\]', str(version), getter_template_copy)
            getter_template_copy = re.sub(r'_SWITCH_TO_VERSION_PLACEHOLDER', switch_method_name, getter_template_copy)
            template_ast_getter = ast.parse(getter_template_copy).body[0]

            setter_template_copy = re.sub(r'\[ATTR\]', attr, setter_template_string)
            setter_template_copy = re.sub(r'\[VERSION\]', str(version), setter_template_copy)
            setter_template_copy = re.sub(r'_SWITCH_TO_VERSION_PLACEHOLDER', switch_method_name, setter_template_copy)
            template_ast_setter = ast.parse(setter_template_copy).body[0]

            out.append(template_ast_getter)
            out.append(template_ast_setter)

    return out
