import argparse

from bench_paths import ensure_project_root_on_path

ensure_project_root_on_path()

from bench_constants import (  # noqa: E402
    DEFAULT_LOOP_COUNT,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_REPEAT_COUNT,
    MODE_CHOICES,
    OUTPUT_FORMATS,
)
from bench_log import log, log_section  # noqa: E402
from config import BenchmarkConfig, OutputConfig  # noqa: E402
from runner import run_benchmarks  # noqa: E402
from reporter import report_results, report_results_switch  # noqa: E402


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="Run the MVO benchmark suite.")
    parser.add_argument("mode", choices=MODE_CHOICES, help="The benchmark mode to run.")
    parser.add_argument(
        "target_name",
        nargs='?',
        default=None,
        help="Optional: Target name for 'suite' or 'perf_overhead' mode.",
    )
    parser.add_argument("--loop", type=int, default=DEFAULT_LOOP_COUNT, help="Number of loops inside the benchmark target.")
    parser.add_argument("--repeat", type=int, default=DEFAULT_REPEAT_COUNT, help="Number of times to repeat the measurement.")
    parser.add_argument(
        "--format",
        type=str,
        default=DEFAULT_OUTPUT_FORMAT,
        choices=OUTPUT_FORMATS,
        help="The output format for the results.",
    )
    return parser.parse_args()


def _log_config(args: argparse.Namespace) -> None:
    log_section("Benchmark configuration:")
    log(f"  mode        : {args.mode}")
    log(f"  target_name : {args.target_name}")
    log(f"  loop        : {args.loop}")
    log(f"  repeat      : {args.repeat}")
    log(f"  format      : {args.format}")
def main():
    """コマンドライン引数を解析し、専門家モジュールに処理を委譲する。"""
    
    # --- 1. コマンドライン引数の解析 ---
    args = parse_args()
    _log_config(args)

    # --- 2. 設定オブジェクトの生成 ---
    bench_config = BenchmarkConfig(
        mode=args.mode,
        target_name=args.target_name,
        loop_count=args.loop,
        repeat_count=args.repeat
    )
    output_config = OutputConfig(format=args.format) 

    # --- 3. ベンチマーク実行 ---
    log("Starting benchmark run...")
    csv_path = run_benchmarks(bench_config)

    # --- 4. グラフ作成 ---
    if csv_path:
        log(f"Results written to: {csv_path}")
        # output_configにmodeを渡して、reporterがグラフの種類を判断できるようにする
        output_config.mode = args.mode
        if args.mode in ('suite', 'gradual', 'perf_overhead'):            
            report_results(csv_path, output_config)
        else:
            report_results_switch(csv_path)
    else:
        log("No results were produced (all targets failed or empty).")

if __name__ == "__main__":
    main()
