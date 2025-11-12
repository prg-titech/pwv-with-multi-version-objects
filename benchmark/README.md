# MVO Benchmark Suite

**Now broken**

## Overview

This directory contains a flexible and automated benchmark suite for measuring the performance overhead of the MVO compiler. It compares the execution time of code processed by our transpiler against an equivalent, handwritten "vanilla" Python implementation.

---

## How to Run Benchmarks

All benchmarks are executed from the project's root directory using the `benchmark/run_benchmark.py` script.

### 1. Running All Benchmarks

To run all available benchmark targets located in the `benchmark/targets/` directory, simply run the script with no arguments:

```bash
python benchmark/run_benchmark.py
```

### 2. Running a Single Benchmark

To run a specific benchmark, provide its directory name as an argument:

```bash
# Runs only the benchmark defined in 'benchmark/targets/01_dispatch/'
python benchmark/run_benchmark.py 01_dispatch
```

### 3. Customizing Benchmark Parameters
You can control the benchmark's precision and duration using command-line options:

- `--loop <count>`: Sets the number of iterations inside the target program's main loop. Defaults to `10000`.

- `--repeat <count>`: Sets the number of times the entire script execution is measured to get a stable average. Defaults to `5`.

- `--format <mode>`: Specify the format for outputting the results. (e.g. `cli`, `graph`)

## How to Create a Benchmark Target

Adding a new benchmark is simple. It requires creating a specific directory structure and a pair of "template" programs.

### 1. Create the Target Directory

First, create a new directory inside `benchmark/targets/`. The name of this directory will be the benchmark's `target_name`.

```bash
benchmark/
└── targets/
    └── 02_sync_overhead/  # <-- Your new benchmark target
```

### 2. Create mvo/ and vanilla/ Subdirectories
Inside your new target directory, create two subdirectories:

- `mvo/`: This will contain the source code to be processed by the mvo compiler.

- `vanilla/`: This will contain the equivalent, handwritten Python code for comparison.

```bash
02_sync_overhead/
├── mvo/
└── vanilla/
```

### 3. Create the Source Files

Place the necessary source files in their respective directories.

- In `mvo/`:

    - Your versioned class files (e.g., `point.py` containing `Point__1__`, `Point__2__`).

    - An optional sync module (e.g., `point_sync.py`).

    - A main entry point file named `main.py`. This file is a template.

- In `vanilla/`:

    - Your handwritten, optimized Python code.

    - A main entry point file, also named `main.py`. This is also a template.

The `main.py` in both directories must be a template that includes a `{LOOP_COUNT}` placeholder. This placeholder will be replaced by the `--loop` value at runtime. The script must also time its own core logic and print the final duration to standard output.

## The Benchmark Pipeline

1. Parse Arguments

2. Prepare

3. Execute

4. Report
