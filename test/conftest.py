import pytest
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent
SAMPLES_ROOT = TEST_ROOT / "resources" / "samples" 

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
