import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .my_lang_transformer import MyLangTransformer
from .scanner import create_project_structure
from .util import logger


INPUT_BASE_PATH = Path("test/resources/samples")
OUTPUT_BASE_PATH = Path("output")
ENTRY_FILE_NAME = "main.py"

def run(sample_dir_name: str):
    """
    Run the transpiler for a given sample directory, and 
    
    Execute the generated code.
    """

    input_dir = INPUT_BASE_PATH / sample_dir_name
    output_dir = OUTPUT_BASE_PATH

    # --- 1. Clean the output directory ---
    if output_dir.exists():
        logger.debug_log(f"Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.debug_log(f"Input directory: {input_dir}")
    logger.debug_log(f"Output directory: {output_dir}")
    
    # --- 2. Scan and Parse the input directory ---
    project_structure = create_project_structure(input_dir)
    logger.success_log(f"Found {len(project_structure['sync_modules'])} sync modules and {len(project_structure['normal_files'])} normal files in {input_dir}.")
    logger.success_log(f"Completed parsing and classifying files in {input_dir}.")

    # --- 3. Transform the ASTs and Write down---
    transformer = MyLangTransformer(project_structure['sync_modules'])
    generated_files = []
    for rel_path, tree in project_structure['normal_files']:
        # a. transform the AST
        transformed_ast = transformer.transform(tree)

        # b. Write the transformed AST back to the output directory
        if transformed_ast:
            output_path = write_single_file(output_dir, rel_path, transformed_ast)
            generated_files.append(output_path)

    # --- 5. Run the generated code ---
    main_file = next((f for f in generated_files if f.name == ENTRY_FILE_NAME), None)
    if main_file:
        output = run_generated_code(main_file, output_dir)
        logger.log(output)
    else:
        logger.error_log(f"No '{ENTRY_FILE_NAME}' found in generated files. Cannot execute.")

def run_for_test(input_dir: Path, temp_output_dir: Path) -> str:
    """
    Run method for testing purposes.
    """
    # --- 1. Scan and Parse the input directory ---
    project_structure = create_project_structure(input_dir)
    
    # --- 2. Transform the ASTs and Write down---
    transformer = MyLangTransformer(project_structure['sync_modules'])
    generated_files = []
    for rel_path, tree in project_structure['normal_files']:
        # a. transform the AST
        transformed_ast = transformer.transform(tree)

        # b. Write the transformed AST back to the output directory
        if transformed_ast:
            output_path = write_single_file(temp_output_dir, rel_path, transformed_ast)
            generated_files.append(output_path)

    # --- 3. Run the generated code ---
    # Pass the output as string
    main_file = next((f for f in generated_files if f.name == 'main.py'), None)
    if main_file:
        output = run_generated_code(main_file, temp_output_dir)
        return output
    return logger.error_log("main.py not generated")

def transpile_directory(input_dir: Path, output_dir: Path) -> list[Path]:
    """
    Run the transpiler for a given input directory, and write results to the output directory.
    No Execution.
    """
    logger.debug_log(f"Input directory: {input_dir}")
    logger.debug_log(f"Output directory: {output_dir}")

    # a. Scan and Organize
    project_structure = create_project_structure(input_dir)
    logger.success_log(f"Found {len(project_structure['sync_modules'])} sync modules and {len(project_structure['normal_files'])} normal files.")

    # b. Prepare and Configure Transformer
    transformer = MyLangTransformer(project_structure['sync_modules'])

    # c. Transform and Write Each Normal File
    generated_files = []
    for rel_path, tree in project_structure['normal_files']:
        transformed_ast = transformer.transform(tree)
        if transformed_ast:
            output_path = write_single_file(output_dir, rel_path, transformed_ast)
            generated_files.append(output_path)
    
    return generated_files

def write_single_file(output_dir: Path, original_rel_path: Path, tree: ast.AST) -> Path:
    """Write a single transformed AST to the specified directory as a file."""
    ast.fix_missing_locations(tree)
    generated_code = ast.unparse(tree)

    output_path = output_dir / original_rel_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(generated_code)

    logger.debug_log(f"Generated: {output_path.resolve()}")
    return output_path

def run_generated_code(main_file: Path, classpath: Path) -> str:
    """Execute the generated main.py file."""
    logger.log("\n--- Running Generated Code ---")
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(classpath.resolve())

        result = subprocess.run(
            [sys.executable, str(main_file.resolve())],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error_log("Execution failed:")
        logger.error_log(e.stderr)
