import ast, re, copy

from .skelton_generator import SkeltonGenerator
from .constructor_generator import ConstructorGenerator
from .stub_method_generator import StubMethodGenerator
from .class_attribute_generator import ClassAttributeGenerator
from ..symbol_table.symbol_table import SymbolTable
from ..util.template_util import get_template_string
from ..util import logger

class UnifiedClassBuilder:
    """
    Orchestrates the transformation of versioned classes' ASTs into a single, unified class AST.
    """
    def __init__(self, class_name: str, state_sync_components: tuple, symbol_table: SymbolTable, incompatibility: dict = None, version_selection_strategy: str = "continuity"):
        self.class_name = class_name
        self.state_sync_components = state_sync_components
        self.incompatibility = incompatibility
        self.symbol_table = symbol_table
        self.version_selection_strategy = version_selection_strategy # continuity | latest
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
        stub_generator = StubMethodGenerator(new_class_ast, self.symbol_table, self.class_name, self.version_selection_strategy)
        stub_generator.generate()

        # --- Inject __getattr__ and __setattr__ methods ---
        self._inject_getattr_setattr(new_class_ast, self.incompatibility)

        # --- Inject state synchronization components ---
        self._inject_sync_components(new_class_ast)

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

    # Preliminary
    def _inject_getattr_setattr(self, new_class_ast: ast.ClassDef, incompatibility: dict = None):
        """
        Injects __getattr__ and __setattr__ methods to handle dynamic attribute access.
        """
        if incompatibility is None:
            return
        getter_template_string = get_template_string("getter_template.py")
        setter_template_string = get_template_string("setter_template.py")
        for version, attr_list in incompatibility.items():
            for attr in attr_list:
                getter_template_copy = copy.deepcopy(getter_template_string)
                setter_template_copy = copy.deepcopy(setter_template_string)
                print(f"Injecting __getattr__ and __setattr__ for attribute '{attr}' in version {version}")
                getter_template_copy = re.sub(r'\[ATTR\]', attr, getter_template_copy)
                getter_template_copy = re.sub(r'\[VERSION\]', str(version), getter_template_copy)
                template_ast_getter = ast.parse(getter_template_copy).body[0]
                setter_template_copy = re.sub(r'\[ATTR\]', attr, setter_template_copy)
                setter_template_copy = re.sub(r'\[VERSION\]', str(version), setter_template_copy)
                template_ast_setter = ast.parse(setter_template_copy).body[0]

                new_class_ast.body.append(template_ast_getter)
                new_class_ast.body.append(template_ast_setter)
