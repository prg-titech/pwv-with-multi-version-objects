import ast

from ..symbol_table.method_info import MethodInfo, ParameterInfo

def _create_slow_path_dispatcher(method_name: str, overloads: list[MethodInfo]) -> list[ast.AST]:
    """
    Generate a static if-elif chain for the slow path dispatcher.
    """

    sorted_overloads = sorted(overloads, key=lambda m: int(m.version))
    
    top_if_stmt = None
    current_if_stmt = None

    for method_info in sorted_overloads:
        # a. Create the if statement condition
        condition = _create_signature_check_condition(method_info.parameters)

        # b. Generate the body of the if block
        if_body = [
            # self.__switch_to_version(...)
            ast.Expr(value=ast.Call(
                func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='_switch_to_version', ctx=ast.Load()),
                args=[ast.Constant(value=str(method_info.version))], keywords=[]
            )),
            # return self._vX_instance.method_name(...)
            ast.Return(value=ast.Call(
                func=ast.Attribute(
                    value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='_current_state', ctx=ast.Load()),
                    attr=method_name, ctx=ast.Load()
                ),
                args=[ast.Starred(value=ast.Name(id='args', ctx=ast.Load()), ctx=ast.Load())],
                keywords=[ast.keyword(arg=None, value=ast.Name(id='kwargs', ctx=ast.Load()))]
            ))
        ]
        
        # c. Create the if-else chain
        if_stmt = ast.If(test=condition, body=if_body, orelse=[])
        if top_if_stmt is None:
            top_if_stmt = if_stmt
            current_if_stmt = top_if_stmt
        else:
            current_if_stmt.orelse = [if_stmt]
            current_if_stmt = if_stmt
    
    # Last else branch: raise TypeError(...)
    if current_if_stmt:
        current_if_stmt.orelse = [ast.Raise(exc=ast.Call(
            func=ast.Name(id='TypeError', ctx=ast.Load()),
            args=[ast.Constant(value=f"No version of '{method_name}' matches the provided arguments.")],
            keywords=[]
        ), cause=None)]

    return [top_if_stmt] if top_if_stmt else []

def _create_signature_check_condition(params: list[ParameterInfo]) -> ast.AST:
    """
    Generates a complex boolean AST expression to statically check if the
    runtime arguments (*args, **kwargs) match the given method signature.
    """
    # --- ASSUMPTIONS ---
    # This logic assumes the target method signature does NOT contain
    # positional-only arguments (/), keyword-only arguments (*),
    # or variadic arguments (*args, **kwargs).
    
    param_names = [p.name for p in params]
    num_params = len(param_names)
    required_param_indices = [i for i, p in enumerate(params) if not p.has_default_value]

    conditions = []

    # Condition 1: The number of positional arguments does not exceed the total number of parameters.
    # e.g., len(args) <= 3
    conditions.append(ast.Compare(
        left=ast.Call(func=ast.Name(id='len', ctx=ast.Load()), args=[ast.Name(id='args', ctx=ast.Load())], keywords=[]),
        ops=[ast.LtE()],
        comparators=[ast.Constant(value=num_params)]
    ))

    # Condition 2: All provided keyword arguments are valid parameter names.
    # e.g., kwargs.keys() <= {'param1', 'param2', ...}
    conditions.append(ast.Compare(
        left=ast.Call(func=ast.Attribute(value=ast.Name(id='kwargs', ctx=ast.Load()), attr='keys', ctx=ast.Load()), args=[], keywords=[]),
        ops=[ast.LtE()],
        comparators=[ast.Set(elts=[ast.Constant(value=name) for name in param_names])]
    ))

    # Condition 3: No parameter is bound by both a positional and a keyword argument.
    # e.g., not (len(args) > 0 and 'param1' in kwargs)
    for i, name in enumerate(param_names):
        conditions.append(ast.UnaryOp(
            op=ast.Not(),
            operand=ast.BoolOp(op=ast.And(), values=[
                ast.Compare(
                    left=ast.Call(func=ast.Name(id='len', ctx=ast.Load()), args=[ast.Name(id='args', ctx=ast.Load())], keywords=[]),
                    ops=[ast.Gt()],
                    comparators=[ast.Constant(value=i)]
                ),
                ast.Compare(
                    left=ast.Constant(value=name),
                    ops=[ast.In()],
                    comparators=[ast.Name(id='kwargs', ctx=ast.Load())]
                )
            ])
        ))

    # Condition 4: All required parameters are satisfied.
    # e.g., (len(args) > 0 or 'param1' in kwargs)
    for i in required_param_indices:
        name = param_names[i]
        conditions.append(ast.BoolOp(op=ast.Or(), values=[
            ast.Compare(
                left=ast.Call(func=ast.Name(id='len', ctx=ast.Load()), args=[ast.Name(id='args', ctx=ast.Load())], keywords=[]),
                ops=[ast.Gt()],
                comparators=[ast.Constant(value=i)]
            ),
            ast.Compare(
                left=ast.Constant(value=name),
                ops=[ast.In()],
                comparators=[ast.Name(id='kwargs', ctx=ast.Load())]
            )
        ]))

    # Condition 5 (Redundant but safe): The total number of bound arguments does not exceed the number of parameters.
    # e.g., len(args) + len(kwargs) <= 3
    conditions.append(ast.Compare(
        left=ast.BinOp(
            left=ast.Call(func=ast.Name(id='len', ctx=ast.Load()), args=[ast.Name(id='args', ctx=ast.Load())], keywords=[]),
            op=ast.Add(),
            right=ast.Call(func=ast.Name(id='len', ctx=ast.Load()), args=[ast.Name(id='kwargs', ctx=ast.Load())], keywords=[])
        ),
        ops=[ast.LtE()],
        comparators=[ast.Constant(value=num_params)]
    ))

    # Combine all conditions with 'and'
    return ast.BoolOp(op=ast.And(), values=conditions)
