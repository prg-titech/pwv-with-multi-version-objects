from pathlib import Path
import ast

from .pipeline import compile_project, execute_generated, transform_project
from .util.constants import DEFAULT_VERSION_SELECTION_STRATEGY

def compile(
    input_dir: Path,
    output_dir: Path,
    *,
    version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY,
    delete_output_dir: bool = True,
) -> None:
    """compile_project() 互換のラッパー。"""
    compile_project(
        input_dir,
        output_dir,
        version_selection_strategy=version_selection_strategy,
        delete_output_dir=delete_output_dir,
    )

def execute(entry_file: str, dir: Path) -> str:
    """execute_generated() 互換のラッパー。"""
    return execute_generated(entry_file, dir)

def transform(
    input_dir: Path,
    *,
    version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY,
) -> list[tuple[Path, ast.AST | None]]:
    """プロジェクトをメモリ上で変換する（versionedクラスのみ）。"""
    return transform_project(
        input_dir,
        version_selection_strategy=version_selection_strategy,
    )
