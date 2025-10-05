import csv
import re
from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt

from config import OutputConfig

def report_results(csv_path: Path, config: OutputConfig):
    """Reads the CSV results and outputs them with the specified format."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        results = [row for row in reader]

    _report_to_cli(results)

    if config.format == 'graph':
        if getattr(config, 'mode', 'suite') == 'gradual':
            _report_to_gradual_line_graph(results, csv_path)
        else:
            _report_to_suite_bar_graph(results, csv_path)

def _report_to_suite_bar_graph(results: list[Dict], csv_path: Path):

    # 1. データを準備し、パフォーマンス倍率を計算
    valid_results = []
    for r in results:
        t_time = float(r['transpiled_time'])
        v_time = float(r['vanilla_time'])
        if t_time > 0 and v_time > 0:
            # 'performance_factor' (何倍遅いか) を計算して、辞書に追加
            r['performance_factor'] = t_time / v_time
            valid_results.append(r)
        
    # パフォーマンス倍率で降順にソート
    sorted_results = sorted(valid_results, key=lambda r: r['performance_factor'], reverse=True)

    if not sorted_results:
        return

    # グラフ描画用にデータを抽出
    target_names = [r['name'] for r in sorted_results]
    factors = [r['performance_factor'] for r in sorted_results]

    # 2. グラフを描画
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.bar(target_names, factors, color='skyblue')
    
    ax.set_xlabel('Benchmark Target')
    # Y軸のラベルを "Performance Factor (x slower)" に変更
    ax.set_ylabel('Performance Factor (x slower)')
    ax.set_title('MyLang Transpiler Performance Factor vs. Vanilla Python')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Y軸の基準線を 1.0 (vanillaと同じ速さ) に引く
    ax.axhline(y=1.0, color='r', linestyle='-')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # 3. グラフをファイルに保存
    output_path = csv_path.parent / "benchmark_results.png"
    plt.savefig(output_path)
    plt.show()

def _report_to_gradual_line_graph(results: list[Dict], csv_path: Path):
    """「段階的オーバーヘッド」モードの結果を折れ線グラフとして保存する。"""
    
    # 1. データを準備し、ターゲット名から横軸の「数値」を抽出
    plot_data = []
    for r in results:
        t_time = float(r['transpiled_time'])
        v_time = float(r['vanilla_time'])
        if t_time > 0 and v_time > 0:
            # ターゲット名の末尾から数値を抽出 (例: "fib20_10000" -> 10000)
            match = re.search(r'_(\d+)$', r['name'])
            if match:
                x_value = int(match.group(1))
                y_value = t_time / v_time
                plot_data.append({'x': x_value, 'y': y_value})
            
    # 2. 横軸の数値で、昇順にソート
    sorted_data = sorted(plot_data, key=lambda d: d['x'])

    if not sorted_data:
        return

    # 3. グラフ描画用にX軸とY軸のデータを抽出
    x_values = [d['x'] for d in sorted_data]
    y_values = [d['y'] for d in sorted_data]
    # 2. 折れ線グラフを描画
    fig, ax = plt.subplots(figsize=(10, 6))
    # X軸とY軸に、カテゴリ名ではなく、数値のリストを渡す
    ax.plot(x_values, y_values, marker='o', linestyle='-', color='dodgerblue')
    
    ax.set_xlabel('Benchmark Parameter (e.g., Problem Size)') # X軸のラベルを汎用的に
    ax.set_ylabel('Performance Factor (x slower)')
    ax.set_title('Performance Factor vs. Benchmark Parameter')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.axhline(y=1.0, color='r', linestyle='-')


    plt.tight_layout()

    # 3. グラフをファイルに保存
    output_path = csv_path.parent / "gradual_overhead_results.png"
    plt.savefig(output_path)

def _report_to_cli(results: list[Dict]):
    """ベンチマーク結果をCLIに表示する。"""
    print("\n\n--- Benchmark Summary ---")
    for result in results:
        name = result['name']
        t_time = float(result['transpiled_time'])
        v_time = float(result['vanilla_time'])
        
        print(f"\nTarget: {name}")
        print(f"  Transpiled MVO:   {t_time:.6f} seconds")
        print(f"  Vanilla Python:   {v_time:.6f} seconds")

        if t_time > 0 and v_time > 0:
            performance_factor = t_time / v_time
            print(f"  Factor: {performance_factor:.2f}x slower")
