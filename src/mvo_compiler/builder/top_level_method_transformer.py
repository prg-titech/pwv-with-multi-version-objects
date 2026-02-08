import ast

from ..util.ast_util import *
from ..util import logger
from ..util.constants import WRAPPER_SELF_ARG_NAME

class TopLevelMethodTransformer(ast.NodeTransformer):
    """
    Transforme the top-level methods' AST of a versioned class.
    - Add _wrapper_self to the method signature.
    - Rebind the original first argument to point to the wrapper
    - Rewrite super() calls
    """
    def __init__(self, class_name: str, parent_context: tuple | None):
        self.class_name = class_name
        self.parent_context = parent_context
        self.is_in_top_level_method = False
        self.top_level_self_name = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if self.is_in_top_level_method:
            self.generic_visit(node)
            return node

        if not node.args.args:
            return node

        self.is_in_top_level_method = True
        self.top_level_self_name = node.args.args[0].arg

        # 1. Add `_wrapper_self` to the method signature
        wrapper_self_arg = ast.arg(arg=WRAPPER_SELF_ARG_NAME)
        if not node.args.kwonlyargs: node.args.kwonlyargs = []
        if not node.args.kw_defaults: node.args.kw_defaults = []
        node.args.kwonlyargs.append(wrapper_self_arg)
        node.args.kw_defaults.append(ast.Constant(value=None))

        # 2. Generate conditional rebinding code: `self = _wrapper_self`
        #    if _wrapper_self is not None:
        #        self = _wrapper_self
        conditional_rebind_stmt = ast.If(
            test=ast.Compare(
                left=ast.Name(id=WRAPPER_SELF_ARG_NAME, ctx=ast.Load()),
                ops=[ast.IsNot()],
                comparators=[ast.Constant(value=None)]
            ),
            body=[
                ast.Assign(
                    targets=[ast.Name(id=self.top_level_self_name, ctx=ast.Store())],
                    value=ast.Name(id=WRAPPER_SELF_ARG_NAME, ctx=ast.Load())
                )
            ],
            orelse=[]
        )

        # 3. Traverse the method body to rewrite super() calls
        new_body = [conditional_rebind_stmt]
        for statement in node.body:
            new_body.append(self.visit(statement))
        node.body = new_body
        
        # 4. Reset state
        self.is_in_top_level_method = False
        self.top_level_self_name = None
        
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        # A nested class definition is found, do not traverse its body
        # (Since, inner classes have their own inheritance and self)
        return node
    
    def visit_Call(self, node: ast.Call) -> ast.Call:
        """
        - Rewrite: super() -> super(ClassName, _wrapper_self)
        """
        if self.is_in_top_level_method and isinstance(node.func, ast.Name) and node.func.id == 'super':
            if not self.parent_context:
                return node
            
            parent_type, parent_info = self.parent_context

            if not node.args: # super()
                if parent_type == 'normal':
                    node.args = [
                        ast.Name(id=self.class_name, ctx=ast.Load()),
                        ast.Name(id=WRAPPER_SELF_ARG_NAME, ctx=ast.Load())
                    ]
                
                elif parent_type == 'mvo':
                    parent_base_name, parent_version = parent_info
                    parent_impl_name = get_impl_class_name(parent_version)
                    
                    node.args = [
                        ast.Attribute(value=ast.Name(id=parent_base_name, ctx=ast.Load()), attr=parent_impl_name, ctx=ast.Load()),
                        ast.Name(id=WRAPPER_SELF_ARG_NAME, ctx=ast.Load())
                    ]
            elif len(node.args) == 2: # super(type, obj)
                logger.warning_log(f"super() with two arguments found in top-level method of versioned class '{self.class_name}'.")
                logger.warning_log("Current implementation only considers the first argument.")
        
        return self.generic_visit(node)
    
