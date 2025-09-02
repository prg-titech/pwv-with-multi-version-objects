import ast
from typing import List

from ..util.ast_util import *
from ..util.template_util import get_template_string
from ...util import logger

BEHAVIOR_INTERFACE_NAME = '_IVersionBehavior'
_SWITCH_TO_VERSION_TEMPLATE = "switch_to_version_template.py"
class StateInfrastructureGenerator:
    """
    Generates the necessary state infrastructure for versioned classes.
    """
    def __init__(self, base_name: str, version_asts: List[ast.AST]):
        self.base_name = base_name
        self.version_asts = version_asts
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
        behavior_interface = self._create_behavior_interface()
        self._create_impl_classes(behavior_interface)
        self._create_state_fields()
        self._create_switch_to_version_method()

        return self.target_class

    def _create_behavior_interface(self) -> ast.ClassDef:
        """Generate the behavior interface."""
        interface_node = ast.ClassDef(
            name=BEHAVIOR_INTERFACE_NAME,
            bases=[ast.Name(id='object', ctx=ast.Load())],
            keywords=[],
            body=[ast.Pass()],
            decorator_list=[]
        )
        self.target_class.body.append(interface_node)
        return interface_node

    def _create_impl_classes(self, behavior_interface: ast.ClassDef):
        """Generate the infrastructure for implementation classes for each version."""
        for cu_ast in self.version_asts:
            original_class_node = get_primary_class_def(cu_ast)
            if not original_class_node: continue

            _, version_num_str = get_class_version_info(original_class_node)
            if not version_num_str: continue

            impl_class = ast.ClassDef(
                name=get_impl_class_name(version_num_str),
                bases=[ast.Name(id=behavior_interface.name, ctx=ast.Load())],
                keywords=[],
                body=[],
                decorator_list=[]
            )
            self.target_class.body.append(impl_class)

    def _create_state_fields(self):
        """Generate a field to hold the current version state."""
        pass

    def _create_switch_to_version_method(self):
        """Generates the _switch_to_version method."""

        template_string = get_template_string(_SWITCH_TO_VERSION_TEMPLATE)
        if not template_string:
            logger.error_log(f"Failed to load switch to version template: {_SWITCH_TO_VERSION_TEMPLATE}")
            return
        template_ast = ast.parse(template_string)

        switch_method_node = template_ast.body[0]

        # If-else structure to switch the current state
        top_if_stmt = None
        current_if_stmt = None

        for cu_ast in self.version_asts:
            original_class_node = get_primary_class_def(cu_ast)
            if not original_class_node: continue
            
            _, version_number = get_class_version_info(original_class_node)
            if not version_number: continue

            # if version_num == {version_number}:
            test_expr = ast.Compare(
                left=ast.Name(id='version_num', ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=version_number)]
            )

            # object_setattr_(self, "_current_state", _version_instances[int(version_num) - 1])
            assign_expr = ast.Expr(value=ast.Call(
                func=ast.Attribute(value=ast.Name(id='object', ctx=ast.Load()), attr='__setattr__', ctx=ast.Load()),
                args=[
                    ast.Name(id='self', ctx=ast.Load()),
                    ast.Constant('_current_state'),
                    ast.Subscript(
                        value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='_version_instances', ctx=ast.Load()),
                        slice=ast.BinOp(
                            left=ast.Call(
                                func=ast.Name(id='int', ctx=ast.Load()),
                                args=[ast.Name(id='version_num', ctx=ast.Load())],
                                keywords=[]
                            ),
                            op=ast.Sub(),
                            right=ast.Constant(value=1)
                        ),
                        ctx=ast.Load()
                    )
                ],
                keywords=[]
            ))
            
            if_stmt = ast.If(test=test_expr, body=[assign_expr], orelse=[])
            
            if top_if_stmt is None:
                top_if_stmt = if_stmt
                current_if_stmt = top_if_stmt
            else:
                current_if_stmt.orelse = [if_stmt]
                current_if_stmt = if_stmt

        if top_if_stmt:
            switch_method_node.body.append(top_if_stmt)

        self.target_class.body.append(switch_method_node)
