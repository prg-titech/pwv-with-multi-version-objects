from typing import Literal

BenchmarkMode = Literal["suite", "gradual", "switch"]
OutputFormat = Literal["cli", "graph"]

OUTPUT_FORMATS = ("cli", "graph")

DEFAULT_LOOP_COUNT = 1
DEFAULT_REPEAT_COUNT = 500
DEFAULT_OUTPUT_FORMAT: OutputFormat = "graph"

MODE_DIR_MAP: dict[BenchmarkMode, str] = {
    "suite": "suite",
    "gradual": "gradual_overhead",
    "switch": "switch_count",
}

MODE_CHOICES = tuple(MODE_DIR_MAP.keys())

TRANSPILED_DIR_NAME = "transpiled"
MVO_DIR_NAME = "mvo"
VANILLA_DIR_NAME = "vanilla"
RESULTS_CSV_NAME = "results_summary.csv"

LOOP_PLACEHOLDER = "{LOOP_COUNT}"
SWITCH_LOOP_COUNT = 1

STRATEGY_CONTINUITY = "continuity"
STRATEGY_LATEST = "latest"
