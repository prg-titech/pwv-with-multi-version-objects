from dataclasses import dataclass

from bench_constants import (
    BenchmarkMode,
    OutputFormat,
    DEFAULT_LOOP_COUNT,
    DEFAULT_REPEAT_COUNT,
    DEFAULT_OUTPUT_FORMAT,
)

@dataclass
class BenchmarkConfig:
    """
    Configuration for running benchmarks.
    """
    mode: BenchmarkMode
    
    target_name: str | None
    
    loop_count: int = DEFAULT_LOOP_COUNT
    
    repeat_count: int = DEFAULT_REPEAT_COUNT

@dataclass
class OutputConfig:
    """
    Configuration for outputting benchmark results.
    """
    format: OutputFormat = DEFAULT_OUTPUT_FORMAT
    
    output_path: str | None = None
    mode: BenchmarkMode | None = None
