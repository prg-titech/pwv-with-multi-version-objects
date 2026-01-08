import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .transformer import SourceTransformer
from .scanner import create_project_structure
from .util import logger

def compile(
        input_dir: Path,
        output_dir: Path,
        *,
        delete_output_dir: bool = True
) -> None:
    """
    Compile the source files in the input directory and write the results to the output directory.

    Args:
        input_dir (Path): The directory containing the source files to compile.
        output_dir (Path): The directory where the compiled files will be written.
        delete_output_dir (bool): Whether to delete the output directory before compilation.
        debug (bool): Whether to enable debug logging.
    """

    # --- 1. Clean the output directory ---
    if output_dir.exists() and delete_output_dir:
        logger.debug_log(f"Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 2. Scan and Parse the input directory ---
    project_structure = create_project_structure(input_dir)
    logger.success_log(f"Found {len(project_structure['sync_modules'])} sync modules and {len(project_structure['normal_files'])} normal files in {input_dir}.")
    logger.success_log(f"Completed parsing and classifying files in {input_dir}.")

    # --- 3. Transform the ASTs and Write down to the output directory ---
    transformer = SourceTransformer(project_structure['sync_modules'], project_structure['incompatibilities'])
    for rel_path, tree in project_structure['normal_files']:
        try:
            # a. transform the AST
            transformed_ast = transformer.transform(tree)
        except Exception as e:
            logger.error_log(f"Error transforming {rel_path}: {e}")
            transformed_ast = None

        # b. Write the transformed AST back to the output directory
        if transformed_ast:
            write_single_file(output_dir, rel_path, transformed_ast)
        else:
            logger.error_log("Something went wrong during transformation; no output generated.")

def execute(
        entry_file: str,
        dir: Path
) -> str:
    """
    Execute the generated entry file.

    Args:
        entry_file (str): The name of the entry file to execute.
        dir (Path): The directory to set as PYTHONPATH.

    Returns:
        str: The standard output from executing the entry file.
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

def write_single_file(output_dir: Path, original_rel_path: Path, tree: ast.AST) -> None:
    """Write a single transformed AST to the specified directory as a file."""
    ast.fix_missing_locations(tree)
    generated_code = ast.unparse(tree)

    output_path = output_dir / original_rel_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(generated_code)

    logger.debug_log(f"Generated: {output_path.resolve()}")
