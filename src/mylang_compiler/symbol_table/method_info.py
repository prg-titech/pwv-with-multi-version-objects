import ast
from dataclasses import dataclass, field
from typing import List

@dataclass
class ParameterInfo:
    """A data class to hold information about a single method parameter."""
    name: str
    type: str
    has_default_value: bool
@dataclass
class MethodInfo:
    """A data class to hold information about a method."""
    name: str
    return_type: str
    version: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    ast_node: ast.FunctionDef | None = None