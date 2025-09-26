import ast
from dataclasses import dataclass, field
from typing import List, Dict, Set

from .method_info import MethodInfo
from .field_info import FieldInfo

@dataclass
class ClassInfo:
    """Holds information about a single class, including all its members."""
    base_name: str
    is_versioned: bool
    base_classes: List[str] = field(default_factory=list)
    methods: Dict[str, List[MethodInfo]] = field(default_factory=dict)
    fields: Dict[str, List[FieldInfo]] = field(default_factory=dict)
    inner_classes: Dict[str, List[ast.ClassDef]] = field(default_factory=dict)

    def get_all_versions(self) -> Set[str]:
        """Get set of all versions of this class."""
        versions = set()
        for overloads in self.methods.values():
            for method_info in overloads:
                versions.add(method_info.version)
        
        for overloads in self.fields.values():
            for field_info in overloads:
                versions.add(field_info.version)
        
        return versions
    
    def get_methods_for_version(self, version_str: str) -> List[MethodInfo]:
        """
        Get all MethodInfo instances that belong to the specified version number.
        """
        version_methods = []
        for overloads in self.methods.values():
            for method_info in overloads:
                if method_info.version == version_str:
                    version_methods.append(method_info)
        return version_methods
    