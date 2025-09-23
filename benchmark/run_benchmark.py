import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from config import BenchmarkConfig, OutputConfig
from preparer import prepare_target
from executor import execute_and_measure
from reporter import report_results

import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- 定数定義 ---
RESULTS_BASE_PATH = PROJECT_ROOT / "benchmark" / "results"
TARGETS_BASE_PATH = PROJECT_ROOT / "benchmark" / "targets"

def main():
    
    # --- 1. Parse the command line arguments ---
    parser = argparse.ArgumentParser(description="Run the MyLang benchmark suite.")
    parser.add_argument("target_name", nargs='?', default=None, 
                        help="Optional: The name of the benchmark target. If omitted, all targets will be run.")
    parser.add_argument("--loop", type=int, default=10000, 
                        help="Number of loops inside the benchmark target's main function.")
    parser.add_argument("--repeat", type=int, default=5, 
                        help="Number of times to repeat the measurement for each target.")
    parser.add_argument("--format", type=str, default='cli', choices=['cli', 'graph'],
                        help="The output format for the results.")
    args = parser.parse_args()

    # --- 2. Generate the configuration instances ---
    bench_config = BenchmarkConfig(
        mode='all' if args.target_name is None else 'single',
        target_name=args.target_name,
        loop_count=args.loop,
        repeat_count=args.repeat
    )
    output_config = OutputConfig(format=args.format) 

    # --- 3. Generate the result directory ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_dir = RESULTS_BASE_PATH / timestamp
    result_dir.mkdir(parents=True)
    
    results_data: List[Dict] = []

    # --- 4. Determine the list of targets to run ---
    if bench_config.mode == 'single':
        targets_to_run = [bench_config.target_name]
    elif bench_config.mode == 'all':
        targets_to_run = [d.name for d in TARGETS_BASE_PATH.iterdir() if d.is_dir()]
    else:
        targets_to_run = []
        
    # --- 5. Run preparation and measurement for each target in sequence ---
    for target_name in targets_to_run:

        target_result_dir = result_dir / target_name
        
        # 5a. Preparation phase
        print(f"\n--- Preparing: {target_name} ---")
        if not prepare_target(target_name, target_result_dir, bench_config):
            continue
        
        # 5b. Measurement phase
        print(f"--- Measuring: {target_name} ---")
        result = execute_and_measure(target_name, target_result_dir, bench_config)
        results_data.append(result)
    
    # --- 6. Save the summary results to a CSV file ---
    if not results_data:
        return
        
    csv_path = result_dir / "results_summary.csv"
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results_data[0].keys())
            writer.writeheader()
            writer.writerows(results_data)
    except (IOError, IndexError) as e:
        return
    
    # --- 7. Display the results ---
    report_results(csv_path, output_config)

if __name__ == "__main__":
    main()