from typing import Dict, Optional

from .class_info import ClassInfo

class SymbolTable:
    """
    Holds information about all classes of the project.
    """

    def __init__(self):
        self._class_table: Dict[str, ClassInfo] = {}

    def add_class(self, class_info: ClassInfo):
        """
        Add or Update class information in the table.
        """
        self._class_table[class_info.base_name] = class_info

    def lookup_class(self, base_name: str) -> Optional[ClassInfo]:
        """
        Search class information by its base name.
        """
        return self._class_table.get(base_name)
    
    def get_representation(self) -> str:
        """
        Gets a string representation of the symbol table.
        """
        lines = ["--- Symbol Table ---"]
        if not self._class_table:
            lines.append("(No classes found)")
            lines.append("--------------------")
            return "\n".join(lines)
        
        for name, info in self._class_table.items():
            lines.append(f"Class: {name} (Versioned: {info.is_versioned})")

            # Output field information
            if not info.fields:
                lines.append("  (No fields found)")
            else:
                for field_name, field_overloads in info.fields.items():
                    for field_info in field_overloads:
                        lines.append(f"  - Field: {field_info.name}, Version: {field_info.version}, Type: {field_info.type}")

            # Output method information
            if not info.methods:
                lines.append("  (No methods found)")
            else:
                for method_name, overloads in info.methods.items():
                    for method_info in overloads:
                        param_types = [p.type for p in method_info.parameters]
                        lines.append(f"  - Method: {method_info.name}, Version: {method_info.version}, Params: {param_types}")
        
        lines.append("--------------------")
        return "\n".join(lines)
