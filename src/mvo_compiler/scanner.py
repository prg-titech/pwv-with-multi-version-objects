import ast
import re
import json
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

from .util import logger
from .util.constants import (
    PROJECT_SYNC_MODULES_KEY,
    PROJECT_INCOMPATIBILITIES_KEY,
    PROJECT_NORMAL_FILES_KEY,
)

def create_project_structure(input_dir: Path) -> Dict:
    """
    1. 入力ディレクトリからPythonファイルを読み取る
    2. 各ファイルをASTに変換する
    3. ファイルを (通常ファイル / 同期関数 / 互換性定義) に分類する
    """
    project_structure = {
        PROJECT_SYNC_MODULES_KEY: {},
        PROJECT_INCOMPATIBILITIES_KEY: {},
        PROJECT_NORMAL_FILES_KEY: []
    }

    py_files = list(input_dir.glob("**/*.py"))
    source_files = []
    state_transformation_files = []
    for file_path in py_files:
        if re.match(r".+_sync\.py$", file_path.name):
            state_transformation_files.append(file_path)
        else:
            source_files.append(file_path)
    incompatibilities_files = list(input_dir.glob("**/*.json"))

    
    # --- 通常ファイル ---
    for source_file in source_files:
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            relative_path = source_file.relative_to(input_dir)
            project_structure[PROJECT_NORMAL_FILES_KEY].append((relative_path, ast.parse(source_code)))
        except Exception as e:
            logger.error_log(f"Failed to parse {source_file}: {e}")

    # --- 状態同期ファイル ---
    sync_pattern = re.compile(r"(.+)_sync\.py$")
    for state_transformation_file in state_transformation_files:
        sync_match = sync_pattern.match(state_transformation_file.name)
        try:
            with open(state_transformation_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            base_name = sync_match.group(1)
            project_structure[PROJECT_SYNC_MODULES_KEY][base_name] = _parse_sync_modules(base_name, source_code)
        except Exception as e:
            logger.error_log(f"Failed to parse {state_transformation_file}: {e}")

    # --- 互換性定義ファイル ---
    for incompatibilities_file in incompatibilities_files:
        try:
            incompatibilities = _parse_incompatibility_json(incompatibilities_file)
            if incompatibilities:
                project_structure[PROJECT_INCOMPATIBILITIES_KEY].update(incompatibilities)
        except Exception as e:
            logger.error_log(f"Failed to parse {incompatibilities_file}: {e}")

    return project_structure


# --------------------
# --- ヘルパー関数 ---
# --------------------

def _parse_sync_modules(base_name: str, source_code: str) -> Tuple:
    tree = ast.parse(source_code)
    modules = []
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules.append(node)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node)
    return (modules, functions)

def _parse_incompatibility_json(file_path: Path) -> Optional[Dict[str, Dict[str, Set[str]]]]:
    """
    JSONスキーマ:
      {
        "<base_name>": {
          "<version>": ["attr1", "attr2", ...]
        }
      }

    戻り値:
      { base_name: { version: set(attrs) } }
    """
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error_log(f"Failed to read/parse json {file_path}: {e}")
        return None

    if not isinstance(data, dict):
        logger.error_log(f"Top-level JSON must be an object: {file_path}")
        return None

    out: Dict[str, Dict[str, Set[str]]] = {}

    for base_name, versions in data.items():
        if not isinstance(base_name, str) or not isinstance(versions, dict):
            logger.error_log(f"Invalid base_name/versions in {file_path}: {base_name}")
            continue

        out[base_name] = {}
        for ver, attrs in versions.items():
            if not isinstance(ver, str):
                logger.error_log(f"Invalid version key in {file_path}: {base_name}.{ver}")
                continue
            if not isinstance(attrs, list) or not all(isinstance(a, str) for a in attrs):
                logger.error_log(f"Invalid attrs list in {file_path}: {base_name}.{ver}")
                continue
            try:
                ver = int(ver)
            except ValueError:
                logger.error_log(f"Version must be an integer string in {file_path}: {base_name}.{ver}")
                continue

            out[base_name][ver] = set(attrs)

    return out
