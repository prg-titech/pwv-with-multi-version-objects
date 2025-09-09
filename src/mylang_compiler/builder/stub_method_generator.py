import ast

from ..symbol_table.symbol_table import SymbolTable
from ..symbol_table.method_info import MethodInfo

from ..util.builder_util import _create_slow_path_dispatcher

class StubMethodGenerator:
    """
    Generates stub methods for the unified class based on the symbol table.
    """
    def __init__(self, target_class: ast.ClassDef, symbol_table: SymbolTable, base_name: str):
        self.target_class = target_class
        self.symbol_table = symbol_table
        self.base_name = base_name

    def generate(self):
        """Generates public stub methods."""
        class_info = self.symbol_table.lookup_class(self.base_name)
        if not class_info:
            return
        
        for method_name, overloads in class_info.methods.items():
            self._generate_stub_for(method_name, overloads)

    # --- HELPER METHODS ---
    def _generate_stub_for(self, method_name: str, overloads: list[MethodInfo]):
        """
        Generates a single stub method with a try-except block for
        fast/slow path dispatch.
        """
        if(method_name == "__initialize__"):
            return


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

        # 2. Create AST for fast path (try block)
        fast_path_body = [ast.Return(value=ast.Call(
            func=ast.Attribute(
                value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='_current_state', ctx=ast.Load()),
                attr=method_name, ctx=ast.Load()
            ),
            args=[ast.Starred(value=ast.Name(id='args', ctx=ast.Load()), ctx=ast.Load())],
            keywords=[
                ast.keyword(arg='_wrapper_self', value=ast.Name(id='self', ctx=ast.Load())),
                ast.keyword(arg=None, value=ast.Name(id='kwargs', ctx=ast.Load()))
            ]
        ))]

        # 3. Create AST for slow path (except block)
        slow_path_body = _create_slow_path_dispatcher(method_name, overloads)
        
        except_handler = ast.ExceptHandler(
            type=ast.Tuple(elts=[ast.Name(id='AttributeError', ctx=ast.Load()), ast.Name(id='TypeError', ctx=ast.Load())], ctx=ast.Load()),
            name=None,
            body=slow_path_body
        )

        # 4. Combine into try-except structure
        stub_method.body = [ast.Try(
            body=fast_path_body,
            handlers=[except_handler],
            orelse=[],
            finalbody=[]
        )]
        
        self.target_class.body.append(stub_method)
