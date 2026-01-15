import sys
import shutil
from pathlib import Path

from config import BenchmarkConfig

PROJECT_ROOT = Path(__file__).parent.parent
TARGETS_BASE_PATH = PROJECT_ROOT / "benchmark" / "targets"
sys.path.append(str(PROJECT_ROOT))

from src.mvo_compiler.mvo_compiler import compile

def _generate_script_from_template(template_path: Path, output_path: Path, loop_count: int):
    """
    Generate an executable Python script from a template.
    """
    template_str = template_path.read_text(encoding='utf-8')
    script_str = template_str.replace('{LOOP_COUNT}', str(loop_count))
    output_path.write_text(script_str, encoding='utf-8')

def prepare_target(target_name: str, result_dir: Path, config: BenchmarkConfig, compile_strategy: str = "continuity") -> bool:
    """
    Prepare the specified benchmark target.
    """
    if config.mode == 'gradual':
        base_path = TARGETS_BASE_PATH / "gradual_overhead"
    elif config.mode == 'suite':
        base_path = TARGETS_BASE_PATH / "suite"
    elif config.mode == 'switch':
        base_path = TARGETS_BASE_PATH / "switch_count"

    target_path = base_path / target_name

    if config.mode == 'gradual' or config.mode == 'suite':
        mvo_source_path = target_path / "mvo"
        vanilla_source_path = target_path / "vanilla"

        if not mvo_source_path.is_dir() or not vanilla_source_path.is_dir():
            print(f"Error: Benchmark target '{target_name}' is incomplete.")
            return False

        transpiled_run_path = result_dir / "transpiled"
        vanilla_run_path = result_dir / "vanilla"
        transpiled_run_path.mkdir(parents=True)
        vanilla_run_path.mkdir(parents=True)
        
        # 1. Transpile & Copy
        compile(mvo_source_path, transpiled_run_path)
        shutil.copytree(vanilla_source_path, vanilla_run_path, dirs_exist_ok=True)
        
        # 2. Generate Scripts from templates
        _generate_script_from_template(
            transpiled_run_path / "main.py", 
            transpiled_run_path / "main.py", 
            config.loop_count
        )
        _generate_script_from_template(
            vanilla_source_path / "main.py", 
            vanilla_run_path / "main.py",
            config.loop_count
        )
    else:
        mvo_source_path = target_path
        transpiled_run_path = result_dir
        compile(mvo_source_path, transpiled_run_path, version_selection_strategy=compile_strategy)
        _generate_script_from_template(
            transpiled_run_path / "main.py", 
            transpiled_run_path / "main.py", 
            1
        )
    return True