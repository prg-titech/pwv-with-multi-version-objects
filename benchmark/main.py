import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.mylang_compiler.run import transpile_directory

TARGETS_BASE_PATH = PROJECT_ROOT / "benchmark" / "targets"
RESULTS_BASE_PATH = PROJECT_ROOT / "benchmark" / "results"
RUNS = 100

def _time_execution(script_path: Path) -> float:
    """
    Run specified script and read execution time from its stdout.
    """
    if not script_path.exists():
        return -1.0

    try:
        # Run main.py
        result = subprocess.run(
            [sys.executable, str(script_path.resolve())],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error running or parsing output from {script_path}: {e}")
        return -1.0

def main():
    parser = argparse.ArgumentParser(description="Run the MyLang benchmark suite.")
    parser.add_argument("target_name", help="The name of the benchmark target to run (e.g., '01_coordinate_transform').")
    args = parser.parse_args()

    # --- 1. Setup ---
    target_path = TARGETS_BASE_PATH / args.target_name
    mylang_path = target_path / "mvo"
    vanilla_path = target_path / "vanilla"

    if not mylang_path.is_dir() or not vanilla_path.is_dir():
        print(f"Error: Benchmark target '{args.target_name}' not found or incomplete.")
        return

    # Create a results directory with a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_dir = RESULTS_BASE_PATH / f"{args.target_name}_{timestamp}"
    transpiled_output_dir = result_dir / "transpiled"
    vanilla_output_dir = result_dir / "vanilla"
    
    transpiled_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"--- Running benchmark: {args.target_name} ---")
    print(f"Results will be stored in: {result_dir}")

    # --- 2. Transpile & Prepare ---
    print("\n1. Transpiling MyLang code...")
    transpile_directory(mylang_path, transpiled_output_dir)

    print("2. Copying vanilla Python code...")
    shutil.copytree(vanilla_path, vanilla_output_dir)

    # --- 3. Execute & Measure ---
    transpiled_main = transpiled_output_dir / "main.py"
    vanilla_main = vanilla_output_dir / "main.py"

    print(f"\n3. Measuring execution time ({RUNS} runs each)...")
    transpiled_time = _time_execution(transpiled_main)
    vanilla_time = _time_execution(vanilla_main)

    # --- 4. Report Results ---
    print("\n--- Benchmark Results ---")
    print(f"Transpiled MyLang:  {transpiled_time:.6f} seconds (average of {RUNS} runs)")
    print(f"Handwritten Python: {vanilla_time:.6f} seconds (average of {RUNS} runs)")
    
    if transpiled_time > 0 and vanilla_time > 0:
        overhead = (transpiled_time / vanilla_time)
        print(f"transpiled/vanilla: {overhead:.2f}")

    # TODO: Write results to a file

if __name__ == "__main__":
    main()
    