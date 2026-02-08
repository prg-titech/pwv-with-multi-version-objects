import ast

from ..symbol_table.symbol_table import SymbolTable
from ..util.ast_util import *
from ..util.template_util import load_template_ast, TemplateRenamer
from ..util.builder_util import _create_slow_path_dispatcher
from ..util import logger
from ..util.constants import INITIALIZE_METHOD_NAME

_CONSTRUCTOR_TEMPLATE = "constructor_template.py"

class ConstructorGenerator:
    """
    Generates the public constructors for the unified class.
    """
    def __init__(self, target_class: ast.ClassDef, symbol_table: SymbolTable, class_name: str):
        self.target_class = target_class
        self.symbol_table = symbol_table
        self.class_name = class_name
        self.template_ast = self._load_template_ast()

    def generate(self):
        """Generate the public __init__ method for the unified class."""
        if not self.template_ast: return

        # 0. Rewrite placeholders in the template AST
        TemplateRenamer(class_name=self.class_name).visit(self.template_ast)

        # 1. Retrieve information for the __initialize__ method from the symbol table
        class_info = self.symbol_table.lookup_class(self.class_name)
        initialize_overloads = class_info.methods.get(INITIALIZE_METHOD_NAME, [])

        # 2. Create a slow path dispatcher (if-elif chain)
        slow_path_body = _create_slow_path_dispatcher(
            self.class_name, INITIALIZE_METHOD_NAME, initialize_overloads
        )
        if not slow_path_body:
            slow_path_body.append(ast.Pass())

        # 3. Replace the body of except block in the template with the generated slow path body
        try_except_node = self.template_ast.body[1]  # Node: try-except
        except_handler = try_except_node.handlers[0] # Node: except
        except_handler.body = slow_path_body # except block body replacement

        # 4. Inject dynamic setup code at the beginning of the template
        self.target_class.body.append(self.template_ast)

    # -- HELPER METHODS --
    def _load_template_ast(self) -> ast.FunctionDef | None:
        template_ast = load_template_ast(_CONSTRUCTOR_TEMPLATE)
        for node in ast.walk(template_ast):
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                return node
        logger.error_log("__init__ not found in constructor template.")
        return None
