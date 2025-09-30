import subprocess
import sys
from pathlib import Path
from typing import Dict

from config import BenchmarkConfig

def _time_execution(script_path: Path, num_repeats: int) -> float:
    """
    Measure the average execution time of the specified script.
    The script is assumed to print the execution time to stdout.
    """
    if not script_path.exists():
        return -1.0

    total_duration = 0.0
    
    for i in range(num_repeats):
        try:
            result = subprocess.run(
                [sys.executable, str(script_path.resolve())],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            total_duration += float(result.stdout.strip())
            
        except (subprocess.CalledProcessError, ValueError) as e:
            return -1.0

    return total_duration / num_repeats


def execute_and_measure(target_name: str, result_dir: Path, config: BenchmarkConfig) -> Dict:
    """
    Measures results of a single benchmark target.
    Returns a dictionary of results.
    A formatted dictionary like:
    {
        "name": str,
        "transpiled_time": float,
        "vanilla_time": float,
        "performance_factor": float
    }
    """
    transpiled_main = result_dir / "transpiled" / "main.py"
    vanilla_main = result_dir / "vanilla" / "main.py"

    transpiled_time = _time_execution(transpiled_main, config.repeat_count)
    vanilla_time = _time_execution(vanilla_main, config.repeat_count)
    
    performance_factor = 0.0
    if transpiled_time > 0 and vanilla_time > 0:
        performance_factor = transpiled_time / vanilla_time

    return {
        "name": target_name,
        "transpiled_time": transpiled_time,
        "vanilla_time": vanilla_time,
        "performance_factor": performance_factor
    }