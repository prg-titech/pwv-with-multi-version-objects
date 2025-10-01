import ast
from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class ParameterInfo:
    """A data class to hold information about a single method parameter."""
    name: str
    type: str
    has_default_value: bool
    kind: Literal[
        'POSITIONAL_ONLY', 
        'POSITIONAL_OR_KEYWORD', 
        'VAR_POSITIONAL', # *args
        'KEYWORD_ONLY', 
        'VAR_KEYWORD'     # **kwargs
    ]

    def __eq__(self, other):
        """
        Custom equality method for ParameterInfo.
        """
        if not isinstance(other, ParameterInfo):
            return NotImplemented

        if self.kind in ('VAR_POSITIONAL', 'VAR_KEYWORD'):
            return self.kind == other.kind
        
        return (self.name == other.name and
                self.type == other.type and
                self.has_default_value == other.has_default_value and
                self.kind == other.kind)

@dataclass
class MethodInfo:
    """A data class to hold information about a method."""
    name: str
    return_type: str
    version: str
    parameters: List[ParameterInfo] = field(default_factory=list)
    ast_node: ast.FunctionDef | None = None