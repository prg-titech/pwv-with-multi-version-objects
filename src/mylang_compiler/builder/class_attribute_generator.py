import ast

from ..symbol_table.symbol_table import SymbolTable

class ClassAttributeGenerator:
    def __init__(self, target_class: ast.ClassDef, symbol_table: SymbolTable, base_name: str):
        self.target_class = target_class
        self.symbol_table = symbol_table
        self.base_name = base_name

    def generate(self):
        class_info = self.symbol_table.lookup_class(self.base_name)
        if not class_info or not class_info.fields:
            return

        final_attributes = {}
        sorted_fields = sorted(
            [field for fields in class_info.fields.values() for field in fields],
            key=lambda f: int(f.version)
        )

        for field_info in sorted_fields:
            if field_info.name not in final_attributes:
                value_node = field_info.initial_value if field_info.initial_value is not None else ast.Constant(value=None)
                
                if field_info.type != "any":
                    attr_stmt = ast.AnnAssign(
                        target=ast.Name(id=field_info.name, ctx=ast.Store()),
                        annotation=ast.Name(id=field_info.type, ctx=ast.Load()),
                        value=value_node,
                        simple=1
                    )
                else:
                    attr_stmt = ast.Assign(
                        targets=[ast.Name(id=field_info.name, ctx=ast.Store())],
                        value=value_node
                    )
                final_attributes[field_info.name] = attr_stmt

        self.target_class.body = list(final_attributes.values()) + self.target_class.body