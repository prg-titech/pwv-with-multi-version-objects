import ast

from .util import ast_util
from .symbol_table.symbol_table import SymbolTable
from .builder.unified_class_builder import UnifiedClassBuilder
from .symbol_table.symbol_table_builder_visitor import SymbolTableBuilderVisitor
from .util import logger

class MyLangTransformer:

    def __init__(self, sync_functions_dict = {}):
        self.sync_functions_dict = sync_functions_dict

    def transform(self, source_ast: ast.AST) -> ast.AST:
        """Transform MyLang AST into Python AST."""

        # --- Pass 1: Construct Symbol Table ---
        symbol_table = SymbolTable()
        analysis_visitor = SymbolTableBuilderVisitor(symbol_table)
        analysis_visitor.visit(source_ast)
        logger.no_header_log(symbol_table.get_representation())

        # --- Pass 2: Group versioned clases ---
        versioned_classes_by_base_name: dict[str, list[ast.ClassDef]] = {}
        for class_node in ast_util.get_all_class_defs(source_ast):
            base_name, _ = ast_util.get_class_version_info(class_node)
            if base_name:
                versioned_classes_by_base_name.setdefault(base_name, []).append(class_node)
        if not versioned_classes_by_base_name:
            return source_ast
        
        # --- Pass 3: Generate unified class AST from each versioned class group ---
        unified_classes: dict[str, ast.ClassDef] = {}
        for base_name, ast_list in versioned_classes_by_base_name.items():
            state_sync_components = self.sync_functions_dict.get(base_name, [])
            builder = UnifiedClassBuilder(base_name, ast_list, state_sync_components, symbol_table)
            unified_class_ast = builder.build()
            unified_classes[base_name] = unified_class_ast
        
        # --- Pass 4: Reconstruct the original AST with unified classes ---
        new_body = []
        processed_base_names = set()
        for node in source_ast.body:
            if isinstance(node, ast.ClassDef):
                base_name, _ = ast_util.get_class_version_info(node)
                if base_name:
                    if base_name not in processed_base_names:
                        new_body.append(unified_classes[base_name])
                        processed_base_names.add(base_name)

                        sync_imports , _ = self.sync_functions_dict.get(base_name, ([], []))
                        for import_node in sync_imports:
                            new_body.insert(0, import_node)
                else:
                    new_body.append(node)
            else:
                new_body.append(node)
        source_ast.body = new_body

        return source_ast
