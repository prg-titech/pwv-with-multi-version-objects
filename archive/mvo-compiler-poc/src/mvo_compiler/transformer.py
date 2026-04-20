import ast

from .util import ast_util
from .symbol_table.symbol_table import SymbolTable
from .builder.unified_class_builder import build_unified_class
from .symbol_table.symbol_table_builder import SymbolTableBuilder
from .util import logger
from .util.constants import DEFAULT_VERSION_SELECTION_STRATEGY

def transform_module(
    source_ast: ast.AST,
    sync_functions_dict: dict,
    incompatibilities: dict | None,
    version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY,
) -> ast.AST:
    """ソースASTを変換して生成ASTを返す（versionedクラスのみ対象）。"""
    symbol_table = _build_symbol_table(source_ast)
    versioned_classes_by_name = _group_versioned_classes(source_ast)
    if not versioned_classes_by_name:
        return source_ast

    unified_classes, all_sync_imports = _build_unified_classes(
        versioned_classes_by_name,
        sync_functions_dict,
        incompatibilities,
        symbol_table,
        version_selection_strategy,
    )

    return _rebuild_module_ast(source_ast, unified_classes, all_sync_imports)

def contains_versioned_classes(source_ast: ast.AST) -> bool:
    return bool(_group_versioned_classes(source_ast))

def _build_symbol_table(source_ast: ast.AST) -> SymbolTable:
    symbol_table = SymbolTable()
    analysis_visitor = SymbolTableBuilder(symbol_table)
    analysis_visitor.visit(source_ast)
    logger.no_header_log(symbol_table.get_representation())
    return symbol_table

def _group_versioned_classes(source_ast: ast.AST) -> dict[str, list[ast.ClassDef]]:
    versioned_classes_by_name: dict[str, list[ast.ClassDef]] = {}
    for node in source_ast.body:
        if isinstance(node, ast.ClassDef):
            class_name, _ = ast_util.get_class_version_info(node)
            if class_name:
                versioned_classes_by_name.setdefault(class_name, []).append(node)
    return versioned_classes_by_name

def _build_unified_classes(
    versioned_classes_by_name: dict[str, list[ast.ClassDef]],
    sync_functions_dict: dict,
    incompatibilities: dict | None,
    symbol_table: SymbolTable,
    version_selection_strategy: str,
) -> tuple[dict[str, ast.ClassDef], list[ast.AST]]:
    unified_classes: dict[str, ast.ClassDef] = {}
    all_sync_imports: list[ast.AST] = []

    for class_name in versioned_classes_by_name:
        state_sync_components = sync_functions_dict.get(class_name, ([], []))
        incompatibility = incompatibilities.get(class_name) if incompatibilities else None

        sync_imports, _ = state_sync_components
        all_sync_imports.extend(sync_imports)

        unified_class_ast = build_unified_class(
            class_name,
            state_sync_components,
            symbol_table,
            incompatibility,
            version_selection_strategy,
        )
        unified_classes[class_name] = unified_class_ast

    return unified_classes, all_sync_imports

def _rebuild_module_ast(
    source_ast: ast.AST,
    unified_classes: dict[str, ast.ClassDef],
    sync_imports: list[ast.AST],
) -> ast.AST:
    new_body: list[ast.AST] = []
    processed_class_names = set()

    final_required_imports = _merge_imports([], sync_imports)
    new_body.extend(final_required_imports)

    for node in source_ast.body:
        if isinstance(node, ast.ClassDef):
            class_name, _ = ast_util.get_class_version_info(node)
            if class_name:
                if class_name not in processed_class_names:
                    new_body.append(unified_classes[class_name])
                    processed_class_names.add(class_name)
            else:
                new_body.append(node)
        else:
            new_body.append(node)
    source_ast.body = new_body

    return source_ast

def _merge_imports(infra_imports: list[ast.AST], sync_imports: list[ast.AST]) -> list[ast.AST]:
    merged = {}
    for imp in infra_imports + sync_imports:
        key = ast.unparse(imp)
        if key not in merged:
            merged[key] = imp
    return list(merged.values())
