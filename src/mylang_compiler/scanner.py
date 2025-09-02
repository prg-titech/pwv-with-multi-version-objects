import ast
import re
from pathlib import Path
from typing import Dict, Tuple

from ..util import logger

def create_project_structure(input_dir: Path) -> Dict:
    """
    1. Read the input directory for Python files
    2. Parse each file to create an AST
    3. Classify files into sync modules and normal files
    """
    source_files = list(input_dir.glob("**/*.py"))
    
    project_structure = {
        "sync_modules": {},
        "normal_files": []
    }

    for file_path in source_files:
        if file_path.is_file():
            _parse_and_classify_file(input_dir, file_path, project_structure)

    return project_structure


# ----------------------
# --- HELPER METHODS ---
# ----------------------

def _parse_and_classify_file(input_dir: Path, file_path: Path, project_structure: Dict):
    """
    Parse the file and update the project_structure dictionary based on its role.
    """
    file_name = file_path.name
    sync_pattern = re.compile(r"(.+)_sync\.py$")

    try:
        sync_match = sync_pattern.match(file_name)

        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        if sync_match:
            # --- Case: Sync Module ---
            base_name = sync_match.group(1)
            project_structure["sync_modules"][base_name] = _parse_sync_modules(base_name, source_code)

        else:
            # --- Case: Normal File ---
            relative_path = file_path.relative_to(input_dir)
            project_structure["normal_files"].append((relative_path, ast.parse(source_code)))

    except Exception as e:
        logger.error_log(f"Failed to parse {file_path}: {e}")

def _parse_sync_modules(base_name: str, source_code: str) -> Tuple:
    tree = ast.parse(source_code)
    modules = []
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.append(node)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node)
    return (modules, functions)
