import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent 
sys.path.append(str(PROJECT_ROOT))

from src.util import logger

SAMPLES_ROOT = Path("test/resources/samples")
EXPECTED_ROOT = Path("test/resources/expected_output")

# File template for the test case
MAIN_PY_TEMPLATE = """
def main():
    # Some main logic here

if __name__ == "__main__":
    main()
"""

def create_test_case(test_case_path: str):
    """
    Create a new test case structure and its expected ouput at the specified path.
    """

    logger.log(f"--- Creating new test case: {test_case_path} ---")

    # --- 1. Create directories for input and expected output ---
    input_dir = SAMPLES_ROOT / test_case_path
    expected_file = (EXPECTED_ROOT / test_case_path).with_suffix('.txt')
    expected_parent_dir = expected_file.parent


    if input_dir.exists():
        logger.error_log(f"Test case directory already exists: {input_dir}")
        logger.log("Aborting to prevent overwriting.")
        return
    if expected_file.exists():
        logger.error_log(f"Expected output file already exists: {expected_file}")
        logger.log("Aborting to prevent overwriting.")
        return

    try:
        input_dir.mkdir(parents=True, exist_ok=True)
        expected_parent_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error_log(f"Failed to create directories: {e}")
        return

    # --- 2. Create main.py and expected.txt files ---
    (input_dir / "main.py").write_text(MAIN_PY_TEMPLATE, encoding="utf-8")
    expected_file.touch()

    logger.log("\nSuccessfully created test case structure:")
    logger.log(f"  - Input:     {input_dir}")
    logger.log(f"  - Expected:  {expected_file}")
    logger.log("\nPlease edit the generated files to define your test.")


def main():
    """
    Parse command-line arguments and Create the test case structure.
    """
    parser = argparse.ArgumentParser(
        description="Create a new test case structure for the MyLang transpiler."
    )
    parser.add_argument(
        "test_case_path",
        help="The relative path for the new test case (e.g., 'features/fields/01_access')."
    )
    args = parser.parse_args()
    
    create_test_case(args.test_case_path)

if __name__ == "__main__":
    main()
