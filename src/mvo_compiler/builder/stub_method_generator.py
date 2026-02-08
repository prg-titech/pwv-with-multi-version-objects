import ast
import copy

from ..symbol_table.symbol_table import SymbolTable
from ..symbol_table.method_info import MethodInfo

from ..util.ast_util import *
from ..util.builder_util import _create_slow_path_dispatcher
from ..util.constants import (
    DEFAULT_VERSION_SELECTION_STRATEGY,
    INITIALIZE_METHOD_NAME,
    VERSION_SELECTION_LATEST,
    WRAPPER_SELF_ARG_NAME,
)

class StubMethodGenerator:
    """
    Generates stub methods for the unified class based on the symbol table.
    """
    def __init__(self, target_class: ast.ClassDef, symbol_table: SymbolTable, base_name: str, version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY):
        self.target_class = target_class
        self.symbol_table = symbol_table
        self.base_name = base_name
        self.version_selection_strategy = version_selection_strategy

    def generate(self):
        """Generates public stub methods."""
        class_info = self.symbol_table.lookup_class(self.base_name)
        if not class_info:
            return
        
        for method_name, overloads in class_info.methods.items():
            if method_name == INITIALIZE_METHOD_NAME:
                continue
        
            if class_info.has_consistent_signature(method_name):
                # A. If signatures are consistent -> Generate stub which completely matches the signature
                self._generate_consistent_signature_stub(method_name, overloads)
            else:
                # B. If signatures are inconsistent -> Generate generic stub with *args, **kwargs
                self._generate_inconsistent_signature_stub(method_name, overloads)


    # --- HELPER METHODS ---
    def _generate_consistent_signature_stub(self, method_name: str, overloads: list[MethodInfo]):
        """
        Generates a stub method with a consistent signature.
        """
        method_info = overloads[0]
        if not method_info.ast_node: return

        # 1. Reconstruct method signature
        stub_args = copy.deepcopy(method_info.ast_node.args)
        stub_args.args[0] = ast.arg(arg='self')
        
        stub_method = ast.FunctionDef(
            name=method_name,
            args=stub_args,
            body=[], decorator_list=[]
        )

        # 1.5
        if self.version_selection_strategy == VERSION_SELECTION_LATEST:
            # self.current_state.version_num
            current_version_num_ast = ast.Attribute(value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=get_current_state_field_name(self.base_name), ctx=ast.Load()), 
                                                attr='_version_number',
                                                ctx=ast.Load())
            
            class_info = self.symbol_table.lookup_class(self.base_name)
            overloads = class_info.methods.get(method_name, [])
            latest_version_num = sorted([int(info.version) for info in overloads])[-1]
            latest_version_num_ast = ast.Constant(value=latest_version_num)

            ast_if = ast.If(
                    test=ast.Compare(
                        left=current_version_num_ast,
                        ops=[ast.NotEq()],
                        comparators=[latest_version_num_ast],
                    ),
                    body=[
                        ast.Expr(
                            value=ast.Call(
                                func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=get_switch_to_version_method_name(self.base_name), ctx=ast.Load()),
                                args=[latest_version_num_ast],
                                keywords=[],
                            )
                        )
                    ],
                    orelse=[],
                )
            
            stub_method.body.append(ast_if)

        # 2. Create AST for fast path (try block)
        call_args = []
        call_keywords = [
            ast.keyword(arg=WRAPPER_SELF_ARG_NAME, value=ast.Name(id='self', ctx=ast.Load()))
        ]

        for param in method_info.parameters:
            if param.kind in ('POSITIONAL_ONLY', 'POSITIONAL_OR_KEYWORD'):
                call_args.append(ast.Name(id=param.name, ctx=ast.Load()))
            elif param.kind == 'KEYWORD_ONLY':
                call_keywords.append(ast.keyword(arg=param.name, value=ast.Name(id=param.name, ctx=ast.Load())))
            elif param.kind == 'VAR_POSITIONAL':
                call_args.append(ast.Starred(value=ast.Name(id=param.name, ctx=ast.Load()), ctx=ast.Load()))
            elif param.kind == 'VAR_KEYWORD':
                call_keywords.append(ast.keyword(arg=None, value=ast.Name(id=param.name, ctx=ast.Load())))
        
        fast_path_call = ast.Call(
            func=ast.Attribute(value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=get_current_state_field_name(self.base_name), ctx=ast.Load()), attr=method_name, ctx=ast.Load()),
            args=call_args,
            keywords=call_keywords
        )
        fast_path_body = [ast.Return(value=fast_path_call)]
        
        # 3. Create AST for slow path (except block)
        # Get all versions which implement this method
        class_info = self.symbol_table.lookup_class(self.base_name)
        overloads = class_info.methods.get(method_name, [])
        callable_versions = sorted([int(info.version) for info in overloads])

        # Currently, we call the first version of sorted callable versions
        if callable_versions:
            next_version_to_try = callable_versions[0]
        else:
            return

        slow_path_body = [
            # a. self._switch_to_version(<next_version_to_try>)
            ast.Expr(value=ast.Call(
                func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=get_switch_to_version_method_name(self.base_name), ctx=ast.Load()),
                args=[ast.Constant(value=next_version_to_try)],
                keywords=[]
            )),
            
            # b. return self._xxx_current_state.method_name(...)
            ast.Return(value=fast_path_call)
        ]

        except_handler = ast.ExceptHandler(type=ast.Name(id='AttributeError', ctx=ast.Load()), name=None, body=slow_path_body)
        
        stub_method.body.append(ast.Try(body=fast_path_body, handlers=[except_handler], orelse=[], finalbody=[]))
        self.target_class.body.append(stub_method)

    def _generate_inconsistent_signature_stub(self, method_name: str, overloads: list[MethodInfo]):
        """
        Generates a generic stub method with *args and **kwargs.
        """
        # 1. Create infrastructure of stub method: def method_name(self, *args, **kwargs)
        stub_method = ast.FunctionDef(
            name=method_name,
            args=ast.arguments(
                posonlyargs=[], args=[ast.arg(arg='self')],
                vararg=ast.arg(arg='args'), kwarg=ast.arg(arg='kwargs'),
                kwonlyargs=[], kw_defaults=[], defaults=[]
            ),
            body=[], decorator_list=[]
        )

        # 1.5
        if self.version_selection_strategy == VERSION_SELECTION_LATEST:
            # self.current_state.version_num
            current_version_num_ast = ast.Attribute(value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=get_current_state_field_name(self.base_name), ctx=ast.Load()), 
                                                attr='_version_number',
                                                ctx=ast.Load())
            
            class_info = self.symbol_table.lookup_class(self.base_name)
            overloads = class_info.methods.get(method_name, [])
            latest_version_num = sorted([int(info.version) for info in overloads])[-1]
            latest_version_num_ast = ast.Constant(value=latest_version_num)

            ast_if = ast.If(
                    test=ast.Compare(
                        left=current_version_num_ast,
                        ops=[ast.NotEq()],
                        comparators=[latest_version_num_ast],
                    ),
                    body=[
                        ast.Expr(
                            value=ast.Call(
                                func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=get_switch_to_version_method_name(self.base_name), ctx=ast.Load()),
                                args=[latest_version_num_ast],
                                keywords=[],
                            )
                        )
                    ],
                    orelse=[],
                )
            
            stub_method.body.append(ast_if)

        # 2. Create AST for fast path (try block)
        fast_path_body = [ast.Return(value=ast.Call(
            func=ast.Attribute(
                value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=get_current_state_field_name(self.base_name), ctx=ast.Load()),
                attr=method_name, ctx=ast.Load()
            ),
            args=[ast.Starred(value=ast.Name(id='args', ctx=ast.Load()), ctx=ast.Load())],
            keywords=[
                ast.keyword(arg=WRAPPER_SELF_ARG_NAME, value=ast.Name(id='self', ctx=ast.Load())),
                ast.keyword(arg=None, value=ast.Name(id='kwargs', ctx=ast.Load()))
            ]
        ))]

        # 3. Create AST for slow path (except block)
        slow_path_body = _create_slow_path_dispatcher(self.base_name, method_name, overloads)
        
        except_handler = ast.ExceptHandler(
            type=ast.Tuple(elts=[ast.Name(id='AttributeError', ctx=ast.Load()), ast.Name(id='TypeError', ctx=ast.Load())], ctx=ast.Load()),
            name=None,
            body=slow_path_body
        )

        # 4. Combine into try-except structure
        stub_method.body.append(ast.Try(
            body=fast_path_body,
            handlers=[except_handler],
            orelse=[],
            finalbody=[]
        ))
        
        self.target_class.body.append(stub_method)
