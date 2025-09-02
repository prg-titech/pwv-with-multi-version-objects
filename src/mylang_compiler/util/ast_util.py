import ast
import re
from typing import Optional, Tuple

VERSIONED_CLASS_PATTERN = re.compile(r"(.+)__(\d+)__$")
UNVERSIONED_CLASS_TAG = "normal"

SWITCH_TO_VERSION_METHOD_NAME = "_switch_to_version"

def get_primary_class_def(tree: ast.AST) -> Optional[ast.ClassDef]:
    """
    Finds and returns the first class definition node from a given AST.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            return node
    return None

def get_all_class_defs(tree: ast.AST) -> list[ast.ClassDef]:
    """
    Returns a list of all class definition nodes in the given AST.
    """
    class_defs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_defs.append(node)
    return class_defs

def get_class_version_info(class_node: ast.ClassDef) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the base name and version number string (e.g., "1", "2") from a class definition node.

    Returns:
        A tuple of (base_name, version_number_string). Returns (None, None) if it's not a versioned class.
    """
    match = VERSIONED_CLASS_PATTERN.match(class_node.name)
    if match:
        base_name = match.group(1)
        version_num_str = match.group(2)
        return base_name, version_num_str
    return None, None

def get_impl_class_name(version_num_str: str) -> str:
    """
    Generates the implementation class name.
    """
    return f"_V{version_num_str}_Impl"

def get_instance_field_name(version_num_str: str) -> str:
    """
    Generates the instance field name.
    """
    return f"_v{version_num_str}_instance"

