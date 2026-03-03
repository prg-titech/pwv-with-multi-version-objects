import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .transformer import transform_module, contains_versioned_classes
from .scanner import create_project_structure
from .util import logger
from .util.constants import DEFAULT_VERSION_SELECTION_STRATEGY
from .util.constants import (
    PROJECT_SYNC_MODULES_KEY,
    PROJECT_INCOMPATIBILITIES_KEY,
    PROJECT_NORMAL_FILES_KEY,
)

def compile_project(
    input_dir: Path,
    output_dir: Path,
    *,
    version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY,
    delete_output_dir: bool = True,
) -> None:
    """
    入力ディレクトリ内のソースをコンパイルし、出力ディレクトリに書き出す。
    """
    # --- 1. 出力ディレクトリのクリーン ---
    if output_dir.exists() and delete_output_dir:
        logger.debug_log(f"Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 2. ASTの変換 ---
    transformed_files = transform_project(
        input_dir,
        version_selection_strategy=version_selection_strategy,
    )

    # --- 3. 出力ディレクトリへ書き出し ---
    for rel_path, transformed_ast, source_code in transformed_files:
        if transformed_ast is not None:
            write_single_file(output_dir, rel_path, tree=transformed_ast)
        elif source_code is not None:
            write_single_file(output_dir, rel_path, source_code=source_code)
        else:
            logger.error_log("Something went wrong during transformation; no output generated.")

def transform_project(
    input_dir: Path,
    *,
    version_selection_strategy: str = DEFAULT_VERSION_SELECTION_STRATEGY,
    project_structure: dict | None = None,
) -> list[tuple[Path, ast.AST | None, str | None]]:
    """
    入力ディレクトリ内のversionedクラスのみを変換し、ASTを返す。
    """
    if project_structure is None:
        project_structure = create_project_structure(input_dir)
    logger.success_log(
        f"Found {len(project_structure[PROJECT_SYNC_MODULES_KEY])} sync modules and {len(project_structure[PROJECT_NORMAL_FILES_KEY])} normal files in {input_dir}."
    )
    logger.success_log(f"Completed parsing and classifying files in {input_dir}.")

    out: list[tuple[Path, ast.AST | None, str | None]] = []
    for rel_path, tree, source_code in project_structure[PROJECT_NORMAL_FILES_KEY]:
        if not contains_versioned_classes(tree):
            logger.debug_log(f"Skipping transform (no versioned classes): {rel_path}")
            out.append((rel_path, None, source_code))
            continue

        try:
            transformed_ast = transform_module(
                tree,
                project_structure[PROJECT_SYNC_MODULES_KEY],
                project_structure[PROJECT_INCOMPATIBILITIES_KEY],
                version_selection_strategy,
            )
        except Exception as e:
            logger.error_log(f"Error transforming {rel_path}: {e}")
            transformed_ast = None

        out.append((rel_path, transformed_ast, None))

    return out

def execute_generated(entry_file: str, dir: Path) -> str:
    """
    生成されたエントリファイルを実行する。
    """
    logger.debug_log("\n--- Running Generated Code ---")
    entry_file_path = dir / entry_file
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(dir.resolve())

        result = subprocess.run(
            [sys.executable, str(entry_file_path.resolve())],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error_log("Execution failed:")
        raise RuntimeError(f"Execution failed for {entry_file_path}: {e.stderr}")

def write_single_file(
    output_dir: Path,
    original_rel_path: Path,
    *,
    tree: ast.AST | None = None,
    source_code: str | None = None,
) -> None:
    """変換後ASTまたは元ソースを指定ディレクトリに1ファイル書き出す。"""
    if tree is None and source_code is None:
        raise ValueError("Either tree or source_code must be provided.")
    if tree is not None and source_code is not None:
        raise ValueError("Only one of tree or source_code can be provided.")
    if tree is not None:
        ast.fix_missing_locations(tree)
        generated_code = ast.unparse(tree)
    else:
        generated_code = source_code

    output_path = output_dir / original_rel_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(generated_code)

    logger.debug_log(f"Generated: {output_path.resolve()}")
