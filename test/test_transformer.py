import sys
from pathlib import Path

from src.mylang_compiler.run import run_for_test

sys.path.append(str(Path(__file__).parent.parent / 'src'))

SAMPLES_ROOT = Path("test/resources/samples")
EXPECTED_ROOT = Path("test/resources/expected_output")

def test_transpilation_and_execution(input_dir: Path, tmp_path: Path):
    """
    Each test case will run the transpiler and execute the generated code,
    then compare the output with the expected output.

    The "input_dir" argument is dynamically provided by conftest.py.
    """
    # --- 1. Arrange ---
    relative_path = input_dir.relative_to(SAMPLES_ROOT)
    expected_output_file = (EXPECTED_ROOT / relative_path.parent).joinpath(relative_path.name + ".txt")
    assert expected_output_file.exists(), f"Expected output file not found: {expected_output_file}"
        
    expected_output = expected_output_file.read_text(encoding="utf-8")

    # --- 2. Act ---
    actual_output = run_for_test(input_dir, tmp_path)

    # --- 3. Assert ---
    assert expected_output.strip().replace('\r\n', '\n') == actual_output.strip().replace('\r\n', '\n'), "Runtime output does not match expected output."
