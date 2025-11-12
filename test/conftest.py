import pytest

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = PROJECT_ROOT / "test"
SAMPLES_ROOT = TEST_ROOT / "resources" / "samples"
EXPECTED_ROOT = TEST_ROOT / "resources" / "expected_output"

def pytest_addoption(parser):
    """Adds the --target_dir command-line option to pytest."""
    parser.addoption(
        "--target_dir", action="store", default="", help="Run tests only on a specific directory"
    )

def pytest_generate_tests(metafunc):
    """
    Dynamically generates test cases based on the --target_dir option.
    This hook is called by pytest during test collection.
    """

    if "input_dir" in metafunc.fixturenames:
        target_path_str = metafunc.config.getoption("--target_dir")
        
        search_root = SAMPLES_ROOT
        if target_path_str:
            search_root = SAMPLES_ROOT / target_path_str

        if not search_root.is_dir():
            pytest.fail(f"Test case directory not found: {search_root}")

        # Collect directories that contain Python files
        main_py_files = list(search_root.glob("**/main.py"))
        test_case_dirs = [p.parent for p in main_py_files]
        if not test_case_dirs:
            pytest.fail(f"No test cases (directories with a main.py) found in {search_root}")

        # Parametrize the test function with the collected directories
        metafunc.parametrize(
            "input_dir", 
            test_case_dirs, 
            ids=[str(p.relative_to(SAMPLES_ROOT)) for p in test_case_dirs]
        )

DEBUG_MODE = False

def debug_log(message: str):
    """Prints a debug message."""
    if DEBUG_MODE:
        print(f"[LOG]     {message}")

def success_log(message: str):
    """Prints a success message."""
    if DEBUG_MODE:
        print(f"[SUCCESS] {message}")

def error_log(message: str):
    """Prints an error message."""
    print(f"[ERROR]   {message}")

def no_header_log(message: str):
    """Prints a message without a header."""
    print(message)

def log(message: str):
    """Prints a general message that should always be visible."""
    print(message)
