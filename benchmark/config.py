from dataclasses import dataclass
from typing import Literal

@dataclass
class BenchmarkConfig:
    """
    Configuration for running benchmarks.
    """
    mode: Literal['all', 'single']
    
    target_name: str | None
    
    loop_count: int = 10000
    
    repeat_count: int = 5

@dataclass
class OutputConfig:
    """
    Configuration for outputting benchmark results.
    """
    format: Literal['cli', 'graph'] = 'cli'
    
    output_path: str | None = None