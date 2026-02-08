from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple

from .method_info import MethodInfo

@dataclass
class ClassInfo:
    """Holds information about a single class, including all its members."""
    class_name: str
    is_versioned: bool
    versioned_bases: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)
    methods: Dict[str, List[MethodInfo]] = field(default_factory=dict)

    def get_all_versions(self) -> Set[str]:
        """
        Get set of all versions of this class.
        """
        versions = set()
        for overloads in self.methods.values():
            for method_info in overloads:
                versions.add(method_info.version)
        
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

    def has_consistent_signature(self, method_name: str) -> bool:
        """
        Check if all versions of the specified method have a consistent signature.
        """
        overloads = self.methods.get(method_name)
        if not overloads or len(overloads) <= 1:
            return True

        first_signature = overloads[0].parameters
        for other_info in overloads[1:]:
            if other_info.parameters != first_signature:
                return False
        
        return True
        
