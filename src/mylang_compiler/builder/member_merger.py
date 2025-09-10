import ast
import copy
from typing import List, Optional

from .self_rewrite_visitor import SelfRewriteVisitor
from ..util.ast_util import *
from ..util import logger

class MemberMerger:
    """
    Copy members from versioned classes to their corresponding implementation classes.
    """
    def __init__(self, target_class: ast.ClassDef, version_asts: List[ast.AST]):
        self.target_class = target_class
        self.version_asts = version_asts

    def merge(self):
        """Merge members from versioned classes into their implementation classes."""
        self_rewriter = SelfRewriteVisitor()

        for version_ast in self.version_asts:
            original_class_node = get_primary_class_def(version_ast)
            if not original_class_node:
                continue

            _, version_number = get_class_version_info(original_class_node)
            if not version_number:
                continue

            has_original_constructor = self._has_user_defined_constructor(original_class_node)

            # Find the corresponding implementation class (_V1_Impl, etc.)
            impl_class_name = get_impl_class_name(version_number)
            impl_class_node = self._find_inner_class(impl_class_name)
            if not impl_class_node:
                logger.error_log(f"Could not find implementation class: {impl_class_name}")
                continue

            impl_class_node.body.clear()

            # Copy members from the original class
            for member in original_class_node.body:
                member_copy = copy.deepcopy(member)

                # if the member is a function named __init__, rename it to __initialize__
                if isinstance(member_copy, ast.FunctionDef) and member_copy.name == '__init__':
                    member_copy.name = '__initialize__'

                # Rewrite 'self' references in method signatures and bodies
                transformed_method = self_rewriter.visit(member_copy)
                impl_class_node.body.append(transformed_method)

            # Inject the version number as an attribute
            # e.g., _version_number = 1
            version_attr_stmt = ast.Assign(
                targets=[ast.Name(id='_version_number', ctx=ast.Store())],
                value=ast.Constant(value=str(version_number))
            )
            impl_class_node.body.insert(0, version_attr_stmt) 

            # Inject a default constructor
            if not has_original_constructor:
                self._ensure_default_constructor(impl_class_node)

    # -- HELPER METHODS --
    def _find_inner_class(self, name: str) -> Optional[ast.ClassDef]:
        """Finds the inner implementation class with the given name."""
        for node in self.target_class.body:
            if isinstance(node, ast.ClassDef) and node.name == name:
                return node
        return None
    
    def _has_user_defined_constructor(self, class_node: ast.ClassDef) -> bool:
        """Checks if the class has a user-defined constructor (__init__ method)."""
        return any(
            isinstance(node, ast.FunctionDef) and node.name == '__init__'
            for node in class_node.body
        )

    def _ensure_default_constructor(self, impl_class_node: ast.ClassDef):
        """Adds an empty default constructor."""
        default_ctor = ast.FunctionDef(
            name='__init__',
            args=ast.arguments(posonlyargs=[], args=[ast.arg(arg='self')], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=[ast.Pass()],
            decorator_list=[]
        )
        impl_class_node.body.append(default_ctor)
