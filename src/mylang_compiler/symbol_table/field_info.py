import ast
from dataclasses import dataclass

@dataclass
class FieldInfo:
    """Holds information about a single class field."""
    name: str
    type: str
    version: str # e.g., "v1", "v2", or "normal"
    initial_value: ast.AST | None = None
