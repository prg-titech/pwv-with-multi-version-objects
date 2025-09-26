import ast

from .symbol_table import SymbolTable
from .class_info import ClassInfo
from .method_info import MethodInfo, ParameterInfo
from .field_info import FieldInfo
from ..util.ast_util import get_class_version_info, UNVERSIONED_CLASS_TAG

class SymbolTableBuilder(ast.NodeVisitor):
    """
    Traverses the MyLang AST to build a symbol table.
    """
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name = node.name
        base_name, version = get_class_version_info(node)

        if not base_name:
            # Unversioned class
            base_name = class_name
            is_versioned = False
            version = UNVERSIONED_CLASS_TAG
        else:
            is_versioned = True

        existing_class_info = self.symbol_table.lookup_class(base_name)
        methods_map = existing_class_info.methods if existing_class_info else {}
        fields_map = existing_class_info.fields if existing_class_info else {}
        inner_classes_map = existing_class_info.inner_classes if existing_class_info else {}
        base_class_names = existing_class_info.base_classes if existing_class_info else []
        
        for member in node.body:
            # Collect methods
            if isinstance(member, ast.FunctionDef):
                method_info = self._create_method_info(member, version)
                if member.name == '__init__' and is_versioned:
                    method_info.name = '__initialize__'
                    method_info.ast_node.name = '__initialize__'
                methods_map.setdefault(method_info.name, []).append(method_info)

            # Collect class fields with type hints (e.g., x: int = 1)
            elif isinstance(member, ast.AnnAssign):
                if isinstance(member.target, ast.Name):
                    field_info = self._create_field_info_from_ann_assign(member, version)
                    fields_map.setdefault(member.target.id, []).append(field_info)
            
            # Collect class fields with no type hints (e.g., x = 1)
            elif isinstance(member, ast.Assign):
                for target in member.targets:
                    if isinstance(target, ast.Name):
                        field_info = self._create_field_info_from_assign(target.id, member, version)
                        fields_map.setdefault(target.id, []).append(field_info)

            # Collect inner classes
            elif isinstance(member, ast.ClassDef):
                inner_classes_map.setdefault(member.name, []).append(member)


        base_class_names = list(set(base_class_names + [base.id for base in node.bases if isinstance(base, ast.Name)]))

        class_info = ClassInfo(base_name, is_versioned, base_class_names, methods_map, fields_map)
        self.symbol_table.add_class(class_info)

    # --- HELPER METHODS ---
    def _create_method_info(self, method_node: ast.FunctionDef, version: str) -> MethodInfo:
        parameters = []
        # Calculate the number of default arguments for the method
        num_defaults = len(method_node.args.defaults)
        num_params = len(method_node.args.args)

        for i, arg in enumerate(method_node.args.args):
            if arg.arg == 'self':
                continue

            # Check if the parameter has a default value
            has_default = (i >= num_params - num_defaults)

            param_info = ParameterInfo(
                name=arg.arg,
                type=ast.unparse(arg.annotation) if arg.annotation else "any",
                has_default_value=has_default
            )
            parameters.append(param_info)

        return MethodInfo(
            name=method_node.name,
            return_type=ast.unparse(method_node.returns) if method_node.returns else "any",
            version=version,
            parameters=parameters,
            ast_node=method_node
        )

    def _create_field_info_from_ann_assign(self, field_node: ast.AnnAssign, version: str) -> FieldInfo:
        return FieldInfo(
            name=field_node.target.id,
            type=ast.unparse(field_node.annotation),
            version=version,
            initial_value=field_node.value
        )

    def _create_field_info_from_assign(self, name: str, assign_node: ast.Assign, version: str) -> FieldInfo:
        return FieldInfo(
            name=name,
            type="any",
            version=version,
            initial_value=assign_node.value
        )
