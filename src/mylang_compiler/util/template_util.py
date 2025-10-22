from pathlib import Path
from . import logger
import ast

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

def get_template_string(template_filename: str) -> str | None:
    """
    Read the contents of the specified template file in the templates directory.

    Args:
        template_filename: The name of the template file to read (e.g., "stub_method_template.py")

    Returns:
        The contents of the file as a string, or None if the file is not found.
    """
    template_path = _TEMPLATE_DIR / template_filename
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error_log(f"Template file not found at: {template_path}")
        return None
    
def load_template_ast(template_filename: str) -> ast.Module | None:
    """
    Load and parse the AST from the specified template file.

    Args:
        template_filename: The name of the template file to read (e.g., "stub_method_template.py")

    Returns:
        The parsed AST Module node, or None if loading or parsing fails.
    """
    template_string = get_template_string(template_filename)
    if not template_string:
        logger.error_log(f"Failed to load template: {template_filename}")
        return None

    try:
        template_ast = ast.parse(template_string)
        return template_ast
    except SyntaxError as e:
        logger.error_log(f"Syntax error parsing template {template_filename}: {e}")
        return None
