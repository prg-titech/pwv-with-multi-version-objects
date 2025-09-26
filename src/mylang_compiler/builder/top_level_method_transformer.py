import ast

_WRAPPER_SELF_ARG_NAME = '_wrapper_self'

class TopLevelMethodTransformer(ast.NodeTransformer):

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:

        original_self_name = node.args.args[0].arg

        wrapper_self_arg = ast.arg(arg=_WRAPPER_SELF_ARG_NAME)
        if not node.args.kwonlyargs:
            node.args.kwonlyargs = []
        if not node.args.kw_defaults:
            node.args.kw_defaults = []
        node.args.kwonlyargs.append(wrapper_self_arg)
        node.args.kw_defaults.append(ast.Constant(value=None))

        rebinding_stmt = ast.Assign(
            targets=[ast.Name(id=original_self_name, ctx=ast.Store())],
            value=ast.Name(id=_WRAPPER_SELF_ARG_NAME, ctx=ast.Load())
        )

        node.body.insert(0, rebinding_stmt)
        
        return node
