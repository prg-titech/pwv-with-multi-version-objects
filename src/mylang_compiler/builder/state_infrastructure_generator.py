import ast
from typing import List

from ..util.ast_util import *
from ..util.template_util import get_template_string
from ..util import logger

_SWITCH_TO_VERSION_TEMPLATE = "switch_to_version_template.py"
class StateInfrastructureGenerator:
    """
    Generates the necessary state infrastructure for versioned classes.
    """
    def __init__(self, base_name: str, version_asts: List[ast.AST], state_sync_function_asts: List[ast.FunctionDef]):
        self.base_name = base_name
        self.version_asts = version_asts
        self.state_sync_function_asts = state_sync_function_asts
        self.target_class = ast.ClassDef(
            name=self.base_name,
            bases=[],
            keywords=[],
            body=[],
            decorator_list=[]
        )

    def generate(self) -> ast.ClassDef:
        """
        Generates the state infrastructure for the versioned class.
        """
        self._create_impl_classes()
        self._create_singleton_instance_list()
        self._create_switch_to_version_method()

        return self.target_class

    def _create_impl_classes(self):
        """Generate the infrastructure for implementation classes for each version."""
        for cu_ast in self.version_asts:
            original_class_node = get_primary_class_def(cu_ast)
            if not original_class_node: continue

            _, version_num_str = get_class_version_info(original_class_node)
            if not version_num_str: continue

            impl_class = ast.ClassDef(
                name=get_impl_class_name(version_num_str),
                bases=[ast.Name(id='object', ctx=ast.Load())],
                keywords=[],
                body=[],
                decorator_list=[]
            )
            self.target_class.body.append(impl_class)

    def _create_singleton_instance_list(self):
        """
        Generate the AST for the class attribute _VERSION_INSTANCES_SINGLETON = [_V1_Impl(), _V2_Impl(), ...]
        """
        impl_class_calls = []
        for tree in self.version_asts:
            class_node = get_primary_class_def(tree)
            if not class_node: continue
            _, version_num = get_class_version_info(class_node)
            if not version_num: continue
            
            impl_name = get_impl_class_name(version_num)
            impl_class_calls.append(
                ast.Call(func=ast.Name(id=impl_name, ctx=ast.Load()), args=[], keywords=[])
            )
        
        singleton_list_stmt = ast.Assign(
            targets=[ast.Name(id='_VERSION_INSTANCES_SINGLETON', ctx=ast.Store())],
            value=ast.List(elts=impl_class_calls, ctx=ast.Load())
        )
        self.target_class.body.append(singleton_list_stmt)

    def _create_switch_to_version_method(self):
        """Generates the _switch_to_version method."""

        template_string = get_template_string(_SWITCH_TO_VERSION_TEMPLATE)
        if not template_string:
            logger.error_log(f"Failed to load switch to version template: {_SWITCH_TO_VERSION_TEMPLATE}")
            return
        template_ast = ast.parse(template_string)

        switch_method_node = template_ast.body[0]

        sync_dispatch_chain = self._create_sync_dispatch_chain()

        for i, node in enumerate(switch_method_node.body):
            if isinstance(node, ast.Assign) and node.targets[0].id == '_SYNC_CALL_PLACEHOLDER_':
                if sync_dispatch_chain:
                    switch_method_node.body[i] = sync_dispatch_chain
                else:
                    # If there are no sync functions, remove the placeholder
                    del switch_method_node.body[i]
                break

        self.target_class.body.append(switch_method_node)

    def _create_sync_dispatch_chain(self) -> ast.If | None:
        """Generates a nested if-else chain to call sync functions."""
        # Create a dictionary with from_ver as key and a list of (to_ver, func_name) tuples as values
        sync_map: dict[str, list[tuple[int, int]]] = {}
        for func_node in self.state_sync_function_asts:
            from_ver, to_ver = get_sync_function_version_info(func_node)
            if from_ver and to_ver:
                sync_map.setdefault(from_ver, []).append((to_ver, func_node.name))

        # Generate the outer if-else chain (if current_version_num == ...:)
        outer_top_if = None
        outer_current_if = None
        for from_ver, to_calls in sync_map.items():
            # Generate the inner if-else chain (if version_num == ...:)
            inner_top_if = None
            inner_current_if = None
            for to_ver, func_name in to_calls:
                inner_if_stmt = ast.If(
                    test=ast.Compare(left=ast.Name(id='version_num', ctx=ast.Load()), ops=[ast.Eq()], comparators=[ast.Constant(value=int(to_ver))]),
                    body=[ast.Expr(value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=func_name, ctx=ast.Load()),
                        args=[ast.Name(id='self', ctx=ast.Load())], keywords=[]
                    ))],
                    orelse=[]
                )
                if inner_top_if is None:
                    inner_top_if = inner_if_stmt
                    inner_current_if = inner_top_if
                else:
                    inner_current_if.orelse = [inner_if_stmt]
                    inner_current_if = inner_if_stmt
            
            # Generate the outer if statement
            outer_if_stmt = ast.If(
                test=ast.Compare(left=ast.Name(id='current_version_num', ctx=ast.Load()), ops=[ast.Eq()], comparators=[ast.Constant(value=int(from_ver))]),
                body=[inner_top_if] if inner_top_if else [ast.Pass()],
                orelse=[]
            )
            if outer_top_if is None:
                outer_top_if = outer_if_stmt
                outer_current_if = outer_top_if
            else:
                outer_current_if.orelse = [outer_if_stmt]
                outer_current_if = outer_if_stmt
                
        return outer_top_if
