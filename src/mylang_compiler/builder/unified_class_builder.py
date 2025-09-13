import ast
from typing import List

from .state_infrastructure_generator import StateInfrastructureGenerator
from .member_merger import MemberMerger
from .constructor_generator import ConstructorGenerator
from .stub_method_generator import StubMethodGenerator
from ..symbol_table.symbol_table import SymbolTable
from ..util.template_util import get_template_string
from ..util import logger

class UnifiedClassBuilder:
    """
    Orchestrates the transformation of versioned classes' ASTs into a single, unified class AST.
    """
    def __init__(self, base_name: str, version_asts: List[ast.AST], state_sync_components: tuple, symbol_table: SymbolTable):
        self.base_name = base_name
        self.version_asts = version_asts
        self.state_sync_components = state_sync_components
        self.symbol_table = symbol_table
        self.new_class_ast: ast.ClassDef = None

    def build(self) -> ast.ClassDef:
        """
        Executes the full build process to generate the unified class AST.
        """
        logger.debug_log(f"Building unified class for: {self.base_name}")

        # --- 1. Generate the skeleton of the new unified class AST ---
        self.state_sync_asts = self.state_sync_components[1] if self.state_sync_components else []
        infra_generator = StateInfrastructureGenerator(self.base_name, self.version_asts, self.state_sync_asts)
        self.new_class_ast = infra_generator.generate()

        # --- 2. Merge versioned classes' members into unified class ---
        member_merger = MemberMerger(self.new_class_ast, self.version_asts)
        member_merger.merge()

        # --- 3. Generate constructor ---
        constructor_generator = ConstructorGenerator(self.new_class_ast, self.version_asts, self.symbol_table)
        constructor_generator.generate()

        # --- 4. Generate stub methods ---
        stub_generator = StubMethodGenerator(self.new_class_ast, self.symbol_table, self.base_name)
        stub_generator.generate()

        # --- 5. Inject state synchronization components ---
        self._inject_sync_components()

        # --- 6. Return the fully constructed class AST ---
        final_ast = ast.Module(
            body = [
                ast.Import(names=[ast.alias(name='inspect', asname=None), ast.alias(name='re', asname=None)]),
                self.new_class_ast
            ],
            type_ignores=[]
        )

        return final_ast
    
    def _inject_method_from_template(self, template_filename: str, method_name: str):
        """
        Injects a specific method definition from a template file into the class AST.
        """
        logger.debug_log(f"Injecting {method_name} method from template.")

        template_string = get_template_string(template_filename)
        if not template_string:
            logger.error_log(f"Failed to load template: {template_filename}")
            return
        template_ast = ast.parse(template_string)

        method_node = next((n for n in ast.walk(template_ast) if isinstance(n, ast.FunctionDef) and n.name == method_name), None)

        if method_node:
            self.new_class_ast.body.append(method_node)
        else:
            logger.error_log(f"{method_name} not found in template file: {template_filename}")

    def _inject_sync_components(self):
        """
        Injects functions and necessary modules from the sync module
        into the unified class as static methods.
        """
        if not self.state_sync_components:
            return

        sync_imports, sync_functions = self.state_sync_components
        logger.debug_log(f"Injecting {len(sync_functions)} sync functions for {self.base_name}")

        for func_node in sync_functions:
            func_node.decorator_list.append(ast.Name(id='staticmethod', ctx=ast.Load()))
            self.new_class_ast.body.append(func_node)
