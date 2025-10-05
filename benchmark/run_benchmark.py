import argparse
from pathlib import Path

from config import BenchmarkConfig, OutputConfig
from runner import run_benchmarks # runnerのメイン関数をインポート
from reporter import report_results

import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

RESULTS_BASE_PATH = PROJECT_ROOT / "benchmark" / "results"
TARGETS_BASE_PATH = PROJECT_ROOT / "benchmark" / "targets"
def main():
    """コマンドライン引数を解析し、専門家モジュールに処理を委譲する。"""
    
    # --- 1. コマンドライン引数の解析 ---
    parser = argparse.ArgumentParser(description="Run the MyLang benchmark suite.")
    parser.add_argument("mode", choices=['suite', 'gradual'], help="The benchmark mode to run.")
    parser.add_argument("target_name", nargs='?', default=None, help="Optional: Target name for 'suite' mode.")
    parser.add_argument("--loop", type=int, default=10000, help="Number of loops inside the benchmark target.")
    parser.add_argument("--repeat", type=int, default=5, help="Number of times to repeat the measurement.")
    parser.add_argument("--format", type=str, default='cli', choices=['cli', 'graph'], help="The output format for the results.")
    args = parser.parse_args()

    # --- 2. 設定オブジェクトの生成 ---
    bench_config = BenchmarkConfig(
        mode=args.mode,
        target_name=args.target_name,
        loop_count=args.loop,
        repeat_count=args.repeat
    )
    output_config = OutputConfig(format=args.format) 

    # --- 3. 実行専門家(runner)に処理を委譲 ---
    csv_path = run_benchmarks(bench_config)

    # --- 4. 結果表示専門家(reporter)に処理を委譲 ---
    if csv_path:
        # output_configにmodeを渡して、reporterがグラフの種類を判断できるようにする
        output_config.mode = args.mode
        report_results(csv_path, output_config)

if __name__ == "__main__":
    main()