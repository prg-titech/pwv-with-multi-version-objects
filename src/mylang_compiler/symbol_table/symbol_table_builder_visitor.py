import ast

from .symbol_table import SymbolTable
from .class_info import ClassInfo
from .method_info import MethodInfo, ParameterInfo
from .field_info import FieldInfo
from ..util.ast_util import get_class_version_info, UNVERSIONED_CLASS_TAG

class SymbolTableBuilderVisitor(ast.NodeVisitor):
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
        
        for member in node.body:
            # Collect methods
            if isinstance(member, ast.FunctionDef):
                method_name = '__initialize__' if member.name == '__init__' else member.name
                
                method_info = self._create_method_info(member, version)
                method_info.name = method_name
                methods_map.setdefault(method_name, []).append(method_info)

            # Collect fields (AnnAssign with type hints)
            elif isinstance(member, ast.AnnAssign):
                # Only public fields are considered (based on name in Python)
                if not member.target.id.startswith('_'):
                     field_info = self._create_field_info_from_ann_assign(member, version)
                     fields_map.setdefault(member.target.id, []).append(field_info)

            # TODO: Collect constructor (__init__) information here

        class_info = ClassInfo(base_name, is_versioned, methods_map, fields_map)
        self.symbol_table.add_class(class_info)

        # Continue traversing the class body
        self.generic_visit(node)

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
            parameters=parameters
        )

    def _create_field_info_from_ann_assign(self, field_node: ast.AnnAssign, version: str) -> FieldInfo:
        return FieldInfo(
            name=field_node.target.id,
            type=ast.unparse(field_node.annotation),
            version=version
        )
