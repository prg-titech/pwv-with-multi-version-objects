from dataclasses import dataclass, field
from typing import List, Dict

from .method_info import MethodInfo
from .field_info import FieldInfo

@dataclass
class ClassInfo:
    """Holds information about a single class, including all its members."""
    base_name: str
    is_versioned: bool
    methods: Dict[str, List[MethodInfo]] = field(default_factory=dict)
    fields: Dict[str, List[FieldInfo]] = field(default_factory=dict)
