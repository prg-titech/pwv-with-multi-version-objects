# PWV with Multi-Version Objects

## Overview

This project is a proof-of-concept (PoC) transpiler for PWV with Multi-Version Objects.

## How It Works

The transpiler orchestrates a full transpile-and-run pipeline, driven by the main entry point (`main.py`).

1.  **Parse**: Parses all `.py` files within a specified test case directory into ASTs using the `ast` module.
2.  **Transform**: Traverses and transforms the ASTs in multiple passes:
    -   **Pass 1 (`SymbolTableBuilderVisitor`):** Builds a `SymbolTable` containing information about all classes, methods, fields, and variables.
    -   **Pass 2 (`UnifiedClassBuilder`):** Merges the versioned class ASTs (e.g., `Test__1__`, `Test__2__`) into a new, unified class AST that implements the State Pattern.
3.  **Generate Code**: Converts the final, transformed ASTs back into well-formatted Python source code.
4.  **Execute**: The test pipeline runs the generated `main.py` to verify its runtime behavior.

## Requirements

-   Python 3.8 or higher
-   **uv**: A fast Python package installer and resolver. See the [installation guide](https://docs.astral.sh/uv/getting-started/).

## Setup and Running

This project uses **uv** for dependency management and reproducibility.  
The environment is defined by `pyproject.toml` and `uv.lock`. Both should be committed to Git.

### First-time setup

```bash
# Pin Python version (creates .python-version)
uv python pin 3.12

# Install dependencies (creates .venv and uv.lock if missing)
uv sync
```

`uv sync` will:
- Create a virtual environment in .venv
- Install project dependencies
- Install the project itself in editable mode (so `src/mylang_compiler` can be imported from anywhere)

### Activating the Environment

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\activate

# deactivate
deactivate
```

### Manual Execution
You can run the transpiler on a specific test case directory using `main.py`.
```bash
# Example: Run the 'basic_cases/basic_01' test case
python main.py basic_cases/basic_01

# Run with debug logs enabled
python main.py basic_cases/basic_01 --debug
```

### Usage Conventions and Limitations

For the transpiler to work correctly, your source code must follow a few specific conventions:

#### 1. Versioned Class Definitions

All versions of a class that you intend to unify must be defined within the **same Python file**. Each versioned class must be named with a double-underscore suffix `__<number>__`.

**Example: `point.py`**
```python
# All versions of 'Point' must be in this single file.

class Point__1__:
    def __init__(self, x: int):
        self.x = x

class Point__2__:
    def __init__(self, r: float):
        self.r = r
```

### 2. Synchronization Function Definitions
If you need to define state transformation logic between versions, you must create a corresponding **synchronization module**.

-   **Naming:** The sync module must be named after the base class, with a `_sync` suffix (e.g., `Point_sync.py`).
-   **Location:** No restriction.

Functions within a sync module are used to transform the state from one version to another. They must follow a strict naming convention and signature.

-   **Naming:** `sync_from_v<source_number>_to_v<target_number>`
-   **Signature:** Each function must accept two arguments: the source implementation instance and the target implementation instance.

**Example: `Point_sync.py`**
```python
def sync_from_v1_to_v2(v1_impl, v2_impl):
    # This function is called when switching from v1 to v2.
    # It should read from v1_impl and write to v2_impl.
    v2_impl.r = v1_impl.x # Example transformation
```

## Automated Tests

This project features a fully automated test suite powered by **pytest**.

### Test Structure

-   **Input Files (`test/resources/samples/`)**: Each subdirectory (e.g., `basic_cases/basic_01/`) represents a self-contained test case and should include all necessary source files.

-   **Expected Output (`test/resources/expected_output/`)**: This directory mirrors the parent structure of `samples/`. The expected runtime output for a given test case is stored in a `.txt` file that shares the same name as the test case directory.
    -   **Example**: The expected output for the test case in `.../samples/basic_cases/basic_01/` should be placed in `.../expected_output/basic_cases/basic_01.txt`.

### Running Tests

-   **Run all tests:**
    ```bash
    pytest
    ```

-   **Run a specific test case:**
    Use the `--target_dir` option to specify the relative path to a single test case.
    ```bash
    # Runs only the tests in the 'basic_cases/basic_01/' directory
    pytest --target_dir=basic_cases/basic_01
    ```

-   **Run with Debug Logs:**
    To see the transpiler's internal logging, add the `--debug` flag.
    ```bash
    pytest --debug --target_dir=basic_cases/basic_01/
    ```

## Directory Structure

A brief overview of the key directories and files in this project.

```
.
├── main.py                          : The main entry point
├── pyproject.toml
├── src/                             : Contains all the source code for the transpiler library
│   └── mylang_compiler/             : The main package for the transpiler
│       ├── run.py                   
│       ├── my_lang_transformer.py
│       ├── builder/                 : A package containing specialized builder classes
│       ├── symbol_table/            : Contains the data structures for the symbol table
│       └── util/                    : Contains shared helper modules like the `logger`
└── tests/                           : Contains all files related to the test suite
    ├── test_transformer.py
    └── resources/                   : Holds all the data required for the tests
        ├── samples/                 : Contains the input `.py` source files for each test case
        └── expected_output/         : Contains the expected output for each corresponding test case
```