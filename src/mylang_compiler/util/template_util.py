from pathlib import Path
from . import logger

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
