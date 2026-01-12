import ast

from .util import ast_util
from .symbol_table.symbol_table import SymbolTable
from .builder.unified_class_builder import UnifiedClassBuilder
from .symbol_table.symbol_table_builder import SymbolTableBuilder
from .util.template_util import load_template_ast
from .util import logger

_REQUIRED_IMPORTS_TEMPLATE = "required_imports_template.py"

class SourceTransformer:
    """Takes the Source AST of **a single file** as input and returns the compiled AST."""
    def __init__(self, sync_functions_dict = {}, incompatibilities = None, version_selection_strategy: str = "continuity"):
        self.sync_functions_dict = sync_functions_dict
        self.incompatibilities = incompatibilities
        self.version_selection_strategy = version_selection_strategy # continuity | latest

    def transform(self, source_ast: ast.AST) -> ast.AST:
        """Transform Source AST into Python AST."""

        # --- Pass 1: Construct Symbol Table ---
        symbol_table = SymbolTable()
        analysis_visitor = SymbolTableBuilder(symbol_table)
        analysis_visitor.visit(source_ast)
        logger.no_header_log(symbol_table.get_representation())

        # --- Pass 2: Group versioned clases ---
        versioned_classes_by_name: dict[str, list[ast.ClassDef]] = {}
        for class_node in ast_util.get_all_class_defs(source_ast):
            class_name, _ = ast_util.get_class_version_info(class_node)
            if class_name:
                versioned_classes_by_name.setdefault(class_name, []).append(class_node)
        if not versioned_classes_by_name:
            return source_ast
        
        # --- Pass 3: Generate unified class AST from each versioned class group ---
        unified_classes: dict[str, ast.ClassDef] = {}
        all_sync_imports = []
        for class_name, _ in versioned_classes_by_name.items():
            state_sync_components = self.sync_functions_dict.get(class_name, ([], []))
            if self.incompatibilities:
                incompatibility = self.incompatibilities[class_name]
            else:
                incompatibility = None
            
            sync_imports, _ = state_sync_components
            all_sync_imports.extend(sync_imports)

            builder = UnifiedClassBuilder(class_name, state_sync_components, symbol_table, incompatibility, self.version_selection_strategy)
            unified_class_ast = builder.build()
            unified_classes[class_name] = unified_class_ast
        
        # --- Pass 4: Reconstruct the original AST with unified classes ---
        new_body = []
        processed_class_names = set()

        required_imports = self._load_required_imports()
        final_required_imports = self._merge_imports(required_imports, all_sync_imports)
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
    
    # --- HELPER METHODS ---
    def _load_required_imports(self) -> list[ast.AST]:
        """Loads the required import AST nodes from the template."""
        imports = []
        template_ast = load_template_ast(_REQUIRED_IMPORTS_TEMPLATE)
        if template_ast:
            for node in template_ast.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)
        return imports

    def _merge_imports(self, infra_imports: list[ast.AST], sync_imports: list[ast.AST]) -> list[ast.AST]:
        merged = {}
        for imp in infra_imports + sync_imports:
            key = ast.unparse(imp)
            if key not in merged:
                merged[key] = imp
        return list(merged.values())
