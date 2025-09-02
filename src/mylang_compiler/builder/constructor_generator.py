import ast
from typing import List

from ..symbol_table.symbol_table import SymbolTable
from ..util.ast_util import *
from ..util.template_util import get_template_string
from ..util.builder_util import _create_slow_path_dispatcher
from ...util import logger

_CONSTRUCTOR_TEMPLATE = "constructor_template.py"

class ConstructorGenerator:
    """
    Generates the public constructors for the unified class.
    """
    def __init__(self, target_class: ast.ClassDef, version_asts: List[ast.AST], symbol_table: SymbolTable):
        self.target_class = target_class
        self.version_asts = sorted(
            version_asts,
            key=lambda ast: get_class_version_info(get_primary_class_def(ast))[1]
        )
        self.symbol_table = symbol_table
        self.template_ast = self._load_template_ast()

    def generate(self):
        """Generate the public __init__ method for the unified class."""
        if not self.template_ast: return

        # 1. Create nodes to be inserted in the template __init__ method
        setup_nodes =  self._create_setup_nodes()

        # 2. Retrieve information for the __initialize__ method from the symbol table
        class_info = self.symbol_table.lookup_class(self.target_class.name)
        initialize_overloads = class_info.methods.get('__initialize__', [])

        # 3. Create a slow path dispatcher (if-elif chain)
        slow_path_body = _create_slow_path_dispatcher(
            '__initialize__', initialize_overloads
        )
        if not slow_path_body:
            slow_path_body.append(ast.Pass())

        # 4. Replace the body of except block in the template with the generated slow path body
        try_except_node = self.template_ast.body[1]  # Node: try-except
        except_handler = try_except_node.handlers[0] # Node: except
        except_handler.body = slow_path_body # except block body replacement

        # 5. Inject dynamic setup code at the beginning of the template
        self.template_ast.body = setup_nodes + [try_except_node]

        # 6. Add the modified __init__ method to the unified class
        self.target_class.body.append(self.template_ast)


    # -- HELPER METHODS --
    def _load_template_ast(self) -> ast.FunctionDef | None:
        template_source = get_template_string(_CONSTRUCTOR_TEMPLATE)
        if not template_source:
            logger.error_log(f"Failed to load constructor template: {_CONSTRUCTOR_TEMPLATE}")
            return None
        template_ast = ast.parse(template_source)
        for node in ast.walk(template_ast):
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                return node
        logger.error_log("__init__ not found in constructor template.")
        return None

    def _create_setup_nodes(self) -> List[ast.AST]:
        setup_nodes = []

        # a. Generate: object.__setattr__(self, '_version_instances', [..])
        impl_class_calls = []
        for tree in self.version_asts:
            class_node = get_primary_class_def(tree)
            if not class_node: continue
            _, version_num = get_class_version_info(class_node)
            if not version_num: continue

            impl_name = get_impl_class_name(version_num)
            impl_class_calls.append(
                ast.Call(func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=impl_name, ctx=ast.Load()), args=[], keywords=[])
            )

        setup_nodes.append(ast.Expr(value=ast.Call(
            func=ast.Attribute(value=ast.Name(id='object', ctx=ast.Load()), attr='__setattr__', ctx=ast.Load()),
            args=[
                ast.Name(id='self', ctx=ast.Load()),
                ast.Constant('_version_instances'),
                ast.List(elts=impl_class_calls, ctx=ast.Load())
            ],
            keywords=[]
        )))

        # b. Generate: object.__setattr__(self, '_current_state', self._version_instances[0])
        setup_nodes.append(ast.Expr(value=ast.Call(
                func=ast.Attribute(value=ast.Name(id='object', ctx=ast.Load()), attr='__setattr__', ctx=ast.Load()),
                args=[
                    ast.Name(id='self', ctx=ast.Load()),
                    ast.Constant('_current_state'),
                    ast.Subscript(
                        value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='_version_instances', ctx=ast.Load()),
                        slice=ast.Constant(value=0),
                        ctx=ast.Load()
                    )
                ],
                keywords=[]
            )))

        return setup_nodes

