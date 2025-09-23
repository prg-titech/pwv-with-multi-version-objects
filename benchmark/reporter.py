import csv
from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt

from config import OutputConfig

def report_results(csv_path: Path, config: OutputConfig):
    """Reads the CSV results and outputs them with the specified format."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        results = [row for row in reader]

    if config.format == 'cli':
        _report_to_cli(results)
    elif config.format == 'graph':
        _report_to_graph(results, csv_path)

def _report_to_graph(results: list[Dict], csv_path: Path):
    valid_results = [r for r in results if float(r['transpiled_time']) > 0 and float(r['vanilla_time']) > 0]
    
    for r in valid_results:
        r['overhead_percent'] = float(r['overhead_percent'])
        
    sorted_results = sorted(valid_results, key=lambda r: r['overhead_percent'], reverse=True)

    target_names = [r['name'] for r in sorted_results]
    overheads = [r['overhead_percent'] for r in sorted_results]

    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.bar(target_names, overheads, color='skyblue')
    
    ax.set_xlabel('Benchmark Target')
    ax.set_ylabel('Performance Overhead (%)')
    ax.set_title('MyLang Transpiler Performance Overhead')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()

    output_path = csv_path.parent / "benchmark_results.png"
    plt.savefig(output_path)


def _report_to_cli(results: list[Dict]):
    """Display results in the command line interface."""
    print("\n\n--- Benchmark Summary ---")
    for result in results:
        name = result['name']
        t_time = float(result['transpiled_time'])
        v_time = float(result['vanilla_time'])
        
        print(f"\nTarget: {name}")
        print(f"  Transpiled MyLang:  {t_time:.6f} seconds")
        print(f"  Handwritten Python: {v_time:.6f} seconds")
        
        if t_time > 0 and v_time > 0:
            overhead = (t_time / v_time - 1) * 100
            print(f"  Overhead: {overhead:.2f}%")