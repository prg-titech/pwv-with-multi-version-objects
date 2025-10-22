import ast

from .skelton_generator import SkeltonGenerator
from .constructor_generator import ConstructorGenerator
from .stub_method_generator import StubMethodGenerator
from .class_attribute_generator import ClassAttributeGenerator
from ..symbol_table.symbol_table import SymbolTable
from ..util.template_util import load_template_ast
from ..util import logger

_VERSION_LOCK_TEMPLATE = "version_lock_template.py"

class UnifiedClassBuilder:
    """
    Orchestrates the transformation of versioned classes' ASTs into a single, unified class AST.
    """
    def __init__(self, class_name: str, state_sync_components: tuple, symbol_table: SymbolTable):
        self.class_name = class_name
        self.state_sync_components = state_sync_components
        self.symbol_table = symbol_table
        self.new_class_ast: ast.ClassDef = None

    def build(self) -> ast.ClassDef:
        """
        Executes the full build process to generate the unified class AST.
        """
        logger.debug_log(f"Building unified class for: {self.class_name}")

        # --- Generate unified class skeleton ---
        sync_asts = self.state_sync_components[1] if self.state_sync_components else []
        skeleton_builder = SkeltonGenerator(self.class_name, self.symbol_table, sync_asts)
        new_class_ast = skeleton_builder.generate()

        # --- Inject class attributes ---
        attr_generator = ClassAttributeGenerator(new_class_ast, self.symbol_table, self.class_name)
        attr_generator.generate()

        # --- Generate constructor ---
        constructor_generator = ConstructorGenerator(new_class_ast, self.symbol_table, self.class_name)
        constructor_generator.generate()

        # --- Generate stub methods ---
        stub_generator = StubMethodGenerator(new_class_ast, self.symbol_table, self.class_name)
        stub_generator.generate()

        # --- Inject state synchronization components ---
        self._inject_sync_components(new_class_ast)

        # --- Inject version lock context manager ---
        template_ast = load_template_ast(_VERSION_LOCK_TEMPLATE)
        
        version_lock_func_ast = None
        for node in ast.walk(template_ast):
            if isinstance(node, ast.FunctionDef) and node.name == 'version_lock':
                version_lock_func_ast = node
                break
        if version_lock_func_ast:
            new_class_ast.body.append(version_lock_func_ast)
        else:
            logger.error_log(f"Method 'version_lock' not found in template: {_VERSION_LOCK_TEMPLATE}")

        # --- Return the fully constructed class AST ---
        final_ast = ast.Module(body=[new_class_ast], type_ignores=[])
        return final_ast

    def _inject_sync_components(self, new_class_ast: ast.ClassDef):
        """
        Injects functions and necessary modules from the sync module
        into the unified class as static methods.
        """
        if not self.state_sync_components:
            return

        _, sync_functions = self.state_sync_components
        logger.debug_log(f"Injecting {len(sync_functions)} sync functions for {self.class_name}")

        for func_node in sync_functions:
            func_node.decorator_list.append(ast.Name(id='staticmethod', ctx=ast.Load()))
            new_class_ast.body.append(func_node)
