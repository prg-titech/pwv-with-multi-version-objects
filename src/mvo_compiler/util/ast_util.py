import ast
import re
from typing import Optional, Tuple

VERSIONED_CLASS_PATTERN = re.compile(r"(.+)__(\d+)__$")
SYNC_FUNC_PATTERN = re.compile(r"_?sync_from_v(\d+)_to_v(\d+)")
UNVERSIONED_CLASS_TAG = "normal"

SWITCH_TO_VERSION_METHOD_NAME = "_switch_to_version"

def get_version_instances_singleton_name(class_name: str) -> str:
    """
    Generates the version instances singleton field name.
    """
    return f"_{class_name.upper()}_VERSION_INSTANCES_SINGLETON"

def get_current_state_field_name(class_name: str) -> str:
    """
    Generates the current state field name.
    """
    return f"_{class_name.lower()}_current_state"

def get_switch_to_version_method_name(class_name: str) -> str:
    """
    Generates the switch to version method name.
    """
    return f"_{class_name.lower()}_switch_to_version"

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

def get_class_version_info_from_name(class_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the base name and version number string (e.g., "1", "2") from a class name.

    Returns:
        A tuple of (base_name, version_number_string). Returns (None, None) if it's not a versioned class.
    """
    match = VERSIONED_CLASS_PATTERN.match(class_name)
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

def get_sync_function_version_info(func_node: ast.FunctionDef) -> Tuple[Optional[int], Optional[int]]:
    """
    Take the AST node of a sync function and extract
    the version number strings of the source (from) and destination (to) from its name
    
    e.g.: 'sync_from_v1_to_v2' -> (1, 2)

    Returns:
        A tuple of (from_version, to_version). Returns (None, None) if the name doesn't match.
    """
    match = SYNC_FUNC_PATTERN.match(func_node.name)
    if match:
        from_version = int(match.group(1))
        to_version = int(match.group(2))
        return from_version, to_version
    return None, None

