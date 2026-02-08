from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = PROJECT_ROOT / "benchmark"
TARGETS_ROOT = BENCH_ROOT / "targets"
RESULTS_ROOT = BENCH_ROOT / "results"


def ensure_project_root_on_path() -> None:
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.append(root)
