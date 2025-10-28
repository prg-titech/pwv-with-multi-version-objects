import ast
import copy
from typing import List

from .top_level_method_transformer import TopLevelMethodTransformer
from ..symbol_table.symbol_table import SymbolTable
from ..util.ast_util import *
from ..util.template_util import TemplateRenamer
from ..util.template_util import load_template_ast
from ..util import logger

_SWITCH_TO_VERSION_TEMPLATE = "switch_to_version_template.py"

class SkeltonGenerator:
    """
    Generates the skelton of unified classes.
    """

    def __init__(self, class_name: str, symbol_table: SymbolTable, sync_asts: List[ast.FunctionDef]):
        self.class_name = class_name
        self.symbol_table = symbol_table
        self.sync_asts = sync_asts
        self.target_class = None

    def generate(self) -> ast.ClassDef:
        class_info = self.symbol_table.lookup_class(self.class_name)
        if not class_info:
            logger.error_log(f"Class '{self.class_name}' not found in symbol table.")
            return None
        
        self._create_class_skeletons(class_info)

        self._merge_methods_into_impl_class(class_info)

        self._create_singleton_instance_list_stmt(class_info)

        self._create_switch_to_version_method()

        return self.target_class


    # --- HELPER METHODS ---
    def _create_class_skeletons(self, class_info):
        # Create a list of unique "parent implementation classes" from ALL versions
        all_unique_base_impls = {}
        for parent_list in class_info.versioned_bases.values():
            for parent_base_name, parent_version in parent_list:
                if parent_version == UNVERSIONED_CLASS_TAG:
                    all_unique_base_impls[parent_base_name] = ast.Name(id=parent_base_name, ctx=ast.Load())
                else:
                    parent_impl_name = get_impl_class_name(parent_version)
                    full_name = f"{parent_base_name}.{parent_impl_name}"
                    all_unique_base_impls[full_name] = ast.Attribute(
                        value=ast.Name(id=parent_base_name, ctx=ast.Load()),
                        attr=parent_impl_name,
                        ctx=ast.Load()
                    )

        # Create the wrapper class definition
        self.target_class = ast.ClassDef(
            name=self.class_name, 
            bases=list(all_unique_base_impls.values()),
            keywords=[], body=[], decorator_list=[]
        )

        for version_str in sorted(class_info.get_all_versions()):
            # Create a list of unique "parent implementation classes" for EACH version
            impl_bases = []
            parent_list = class_info.versioned_bases.get(version_str, [])
            for parent_base_name, parent_version in parent_list:
                if parent_version == UNVERSIONED_CLASS_TAG:
                    impl_bases.append(ast.Name(id=parent_base_name, ctx=ast.Load()))
                else:
                    parent_impl_name = get_impl_class_name(parent_version)
                    impl_bases.append(ast.Attribute(
                        value=ast.Name(id=parent_base_name, ctx=ast.Load()),
                        attr=parent_impl_name,
                        ctx=ast.Load()
                    ))

            # Create the implementation class definition
            impl_class = ast.ClassDef(
                name=get_impl_class_name(version_str),
                bases=impl_bases if impl_bases else [ast.Name(id='object', ctx=ast.Load())],
                keywords=[], body=[], decorator_list=[]
            )
            self.target_class.body.append(impl_class)

    def _merge_methods_into_impl_class(self, class_info):

        for version_str in class_info.get_all_versions():
            impl_class_name = get_impl_class_name(version_str)
            target_impl_class = next((n for n in self.target_class.body if isinstance(n, ast.ClassDef) and n.name == impl_class_name), None)
            if not target_impl_class: continue

            # Create TopLevelMethodTransformer
            parent_info_list = class_info.versioned_bases.get(version_str, [])
            parent_context = None
            if parent_info_list:
                # for simplicity, only consider the first parent
                if len(parent_info_list) > 1:
                    logger.warning_log(f"Multiple inheritance detected in class '{self.class_name}' version '{version_str}'.")
                    logger.warning_log("Current implementation only considers the first parent for method transformation.")
                    logger.warning_log("This may lead to inconsistent behavior compared to Python's method resolution order (MRO).")
                parent_base_name, parent_version = parent_info_list[0]
                if parent_version == UNVERSIONED_CLASS_TAG:
                    parent_context = ('normal', parent_base_name)
                else:
                    parent_context = ('mvo', (parent_base_name, parent_version))
            method_transformer = TopLevelMethodTransformer(self.class_name, parent_context)

            # 1. Merge methods from the versioned class into the impl class
            for method_info in class_info.get_methods_for_version(version_str):
                if method_info.ast_node:
                    member_copy = copy.deepcopy(method_info.ast_node)
                    
                    transformed_method = method_transformer.visit(member_copy)
                    target_impl_class.body.append(transformed_method)

            # 2. Inject _version_number attribute
            version_attr_stmt = ast.Assign(
                targets=[ast.Name(id='_version_number', ctx=ast.Store())],
                value=ast.Constant(value=int(version_str))
            )
            target_impl_class.body.insert(0, version_attr_stmt) 

            # 3. Inject default constructor
            default_ctor = ast.FunctionDef(
                name='__init__',
                args=ast.arguments(posonlyargs=[], args=[ast.arg(arg='self')], kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=[ast.Pass()],
                decorator_list=[]
            )
            target_impl_class.body.append(default_ctor)

    def _create_singleton_instance_list_stmt(self, class_info):
        impl_class_calls = []
        for version_str in sorted(class_info.get_all_versions()):
            impl_name = get_impl_class_name(version_str)
            impl_class_calls.append(
                ast.Call(func=ast.Name(id=impl_name, ctx=ast.Load()), args=[], keywords=[])
            )

        singleton_list_stmt = ast.Assign(
            targets=[ast.Name(id=get_version_instances_singleton_name(class_info.class_name), ctx=ast.Store())],
            value=ast.List(elts=impl_class_calls, ctx=ast.Load())
        )
        self.target_class.body.append(singleton_list_stmt)

    def _create_switch_to_version_method(self):

        template_ast = load_template_ast(_SWITCH_TO_VERSION_TEMPLATE)

        switch_method_node = template_ast.body[0]

        sync_dispatch_chain = self._create_sync_dispatch_chain()

        TemplateRenamer(self.class_name, sync_dispatch_chain).visit(switch_method_node)

        self.target_class.body.append(switch_method_node)

    def _create_sync_dispatch_chain(self) -> ast.If | None:
        """Generates a nested if-else chain to call sync functions."""
        # Create a dictionary with from_ver as key and a list of (to_ver, func_name) tuples as values
        sync_map: dict[str, list[tuple[int, int]]] = {}
        for func_node in self.sync_asts:
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
