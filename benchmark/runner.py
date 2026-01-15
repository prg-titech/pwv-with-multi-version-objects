import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from config import BenchmarkConfig
from preparer import prepare_target
from executor import execute_and_measure, execute_and_measure_for_switch_count

import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

RESULTS_BASE_PATH = PROJECT_ROOT / "benchmark" / "results"
TARGETS_BASE_PATH = PROJECT_ROOT / "benchmark" / "targets"

def run_benchmarks(bench_config: BenchmarkConfig) -> Path | None:
    """
    設定に基づき、適切なベンチマークターゲット群に対して、
    準備・測定のパイプラインを実行し、結果をCSVに保存する。
    """
    # 1. 結果保存用ディレクトリの準備
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_dir = RESULTS_BASE_PATH / timestamp
    result_dir.mkdir(parents=True)
    
    results_data: List[Dict] = []

    # 2. モードに応じて実行対象ターゲットを決定
    if bench_config.mode == 'gradual':
        targets_path = TARGETS_BASE_PATH / "gradual_overhead"
        targets_to_run = sorted([d.name for d in targets_path.iterdir() if d.is_dir()])
    elif bench_config.mode == 'suite':
        targets_path = TARGETS_BASE_PATH / "suite"
        if bench_config.target_name:
            targets_to_run = [bench_config.target_name]
        else:
            targets_to_run = [d.name for d in targets_path.iterdir() if d.is_dir()]
    elif bench_config.mode == 'switch':
        targets_path = TARGETS_BASE_PATH / "switch_count"
        targets_to_run = sorted([d.name for d in targets_path.iterdir() if d.is_dir()])

    # 3. 各ターゲットについて「準備」と「測定」を順番に実行
    if bench_config.mode == 'switch':
        for target_name in targets_to_run:
            target_result_dir0 = result_dir / target_name / "continuity"
            target_result_dir1 = result_dir / target_name / "latest"
            if not prepare_target(target_name, target_result_dir0, bench_config, compile_strategy="continuity"):
                continue
            if not prepare_target(target_name, target_result_dir1, bench_config, compile_strategy="latest"):
                continue

            result = execute_and_measure_for_switch_count(target_name, result_dir / target_name, bench_config)
            results_data.append(result)
    else:
        for target_name in targets_to_run:
            target_result_dir = result_dir / target_name
            
            if not prepare_target(target_name, target_result_dir, bench_config):
                continue
            
            result = execute_and_measure(target_name, target_result_dir, bench_config)
            results_data.append(result)
    
    # 4. 総合結果をCSVファイルに保存
    if not results_data:
        return None
        
    csv_path = result_dir / "results_summary.csv"
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results_data[0].keys())
            writer.writeheader()
            writer.writerows(results_data)
        return csv_path
    except (IOError, IndexError) as e:
        return None