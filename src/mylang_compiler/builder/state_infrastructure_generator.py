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

        self.target_class.body.append(switch_method_node)
