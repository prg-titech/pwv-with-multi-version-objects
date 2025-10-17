import ast

from .symbol_table import SymbolTable
from .class_info import ClassInfo
from .method_info import MethodInfo, ParameterInfo
from .field_info import FieldInfo
from ..util.ast_util import get_class_version_info, get_class_version_info_from_name, UNVERSIONED_CLASS_TAG

class SymbolTableBuilder(ast.NodeVisitor):
    """
    Traverses the MyLang AST to build a symbol table.
    """
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name, version = get_class_version_info(node)

        if not class_name:
            # Unversioned class
            class_name = node.name
            is_versioned = False
            version = UNVERSIONED_CLASS_TAG
        else:
            is_versioned = True

        existing_class_info = self.symbol_table.lookup_class(class_name)
        methods_map = existing_class_info.methods if existing_class_info else {}
        fields_map = existing_class_info.fields if existing_class_info else {}
        inner_classes_map = existing_class_info.inner_classes if existing_class_info else {}
        versioned_bases_map = existing_class_info.versioned_bases if existing_class_info else {}

        # Collect base classes, if this class is versioned
        if is_versioned:
            bases_for_this_version = []
            for base_node in node.bases:
                print(ast.dump(base_node))
                parent_base_name, parent_version = get_class_version_info_from_name(base_node.id)
                
                if not parent_base_name:
                    parent_base_name = ast.unparse(base_node)
                    parent_version = UNVERSIONED_CLASS_TAG
                
                bases_for_this_version.append((parent_base_name, parent_version))
            
            if bases_for_this_version:
                versioned_bases_map[version] = bases_for_this_version
        
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

        class_info = ClassInfo(
            class_name=class_name,
            is_versioned=is_versioned,
            versioned_bases=versioned_bases_map,
            methods=methods_map,
            fields=fields_map,
            inner_classes=inner_classes_map
        )
        self.symbol_table.add_class(class_info)

    # --- HELPER METHODS ---
    def _create_method_info(self, method_node: ast.FunctionDef, version: str) -> MethodInfo:
        parameters = []
        args = method_node.args
        
        # Calculate the starting index of default values
        pos_and_kw_args = args.posonlyargs + args.args
        defaults_start_index = len(pos_and_kw_args) - len(args.defaults)

        # --- 1. Collect positional-only parameters (/) ---
        for i, arg in enumerate(args.posonlyargs):
            parameters.append(ParameterInfo(
                name=arg.arg,
                type=ast.unparse(arg.annotation) if arg.annotation else "any",
                has_default_value=(i >= defaults_start_index),
                kind='POSITIONAL_ONLY'
            ))

        # --- 2. Collect regular parameters ---
        for i, arg in enumerate(args.args):
            # Ignore 'self'
            if i == 0:
                continue
            
            combined_index = len(args.posonlyargs) + i
            parameters.append(ParameterInfo(
                name=arg.arg,
                type=ast.unparse(arg.annotation) if arg.annotation else "any",
                has_default_value=(combined_index >= defaults_start_index),
                kind='POSITIONAL_OR_KEYWORD'
            ))
            
        # --- 3. Collect variable-length positional parameters (*args) ---
        if args.vararg:
            arg = args.vararg
            parameters.append(ParameterInfo(
                name=arg.arg,
                type=ast.unparse(arg.annotation) if arg.annotation else "any",
                has_default_value=False,
                kind='VAR_POSITIONAL'
            ))

        # --- 4. Collect keyword-only parameters (*) ---
        for i, arg in enumerate(args.kwonlyargs):
            has_default = args.kw_defaults[i] is not None
            parameters.append(ParameterInfo(
                name=arg.arg,
                type=ast.unparse(arg.annotation) if arg.annotation else "any",
                has_default_value=has_default,
                kind='KEYWORD_ONLY'
            ))

        # --- 5. Collect variable-length keyword arguments (**kwargs) ---
        if args.kwarg:
            arg = args.kwarg
            parameters.append(ParameterInfo(
                name=arg.arg,
                type=ast.unparse(arg.annotation) if arg.annotation else "any",
                has_default_value=False,
                kind='VAR_KEYWORD'
            ))
        
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
