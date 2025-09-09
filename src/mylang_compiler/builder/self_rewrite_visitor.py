import ast

_WRAPPER_SELF_ARG_NAME = '_wrapper_self'

class SelfRewriteVisitor(ast.NodeTransformer):
    """
    Traverses the AST, updating 'self' references in method signatures and bodies.
    - Renames the original 'self' argument to '_impl_self'.
    - Inserts a new 'self' argument as the second parameter (referring to the wrapper).
    - Updates 'self' references in the method body to point to the new 'self' argument.
    """
    def __init__(self):
        self.original_self_name = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if not node.args.args:
            return node

        # 1. Records the original 'self' argument name and renames it to '_impl_self'.
        original_self_arg = node.args.args[0]
        self.original_self_name = original_self_arg.arg
        original_self_arg.arg = '_impl_self'

        # 2. Inserts a new 'self' argument as the second parameter (referring to the wrapper).
        wrapper_self_arg = ast.arg(arg=_WRAPPER_SELF_ARG_NAME)
        if node.args.kwonlyargs is None:
            node.args.kwonlyargs = []
        node.args.kwonlyargs.append(wrapper_self_arg)

        if node.args.kw_defaults is None:
            node.args.kw_defaults = []
        node.args.kw_defaults.append(ast.Constant(value=None))

        # 3. Traverses the method body (by calling generic_visit, the visit of lower nodes is called)
        self.generic_visit(node)

        self.original_self_name = None
        
        return node
    
    def visit_Name(self, node: ast.Name) -> ast.Name:
        if self.original_self_name and node.id == self.original_self_name:
            return ast.Name(id=_WRAPPER_SELF_ARG_NAME, ctx=node.ctx)

        return node
