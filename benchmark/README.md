# MVO Benchmark Suite

## 概要

このディレクトリには、MVO コンパイラの性能オーバーヘッドを測定するためのベンチマークスイートがあります。トランスパイラで処理したコードと、同等の手書き Python（vanilla）の実行時間を比較します。

---

## 実行方法

ベンチマークはプロジェクトルートから `benchmark/run_benchmark.py` を実行します。

### 0. ベンチマーク用の別環境（推奨）

本体とは別の仮想環境でベンチマークを回す場合は、`bench` 依存グループを使います。

```bash
uv venv .venv-bench
.venv-bench\Scripts\activate
uv sync --group bench --active
```

通常の環境に追加するだけなら、既存の venv で `uv sync --group bench --active` を実行してください。

### 1. 全ベンチマークの実行（モード別）

モード引数が必須です。各モード内の全ターゲットを実行します。

```bash
python benchmark/run_benchmark.py suite
python benchmark/run_benchmark.py gradual
python benchmark/run_benchmark.py switch
python benchmark/run_benchmark.py perf_overhead
```

### 2. 単一ベンチマークの実行（suite / perf_overhead モード）

suite / perf_overhead モードではターゲット名を指定して個別実行できます。

```bash
# 'benchmark/targets/suite/richards/' のみ実行
python benchmark/run_benchmark.py suite richards

# 'benchmark/targets/perf_overhead/method_switch/' のみ実行
python benchmark/run_benchmark.py perf_overhead method_switch
```

### 3. パラメータの指定

コマンドラインオプションで測定の精度と時間を調整できます。

- `--loop <count>`: 対象プログラムのメインループの反復回数。デフォルトは `1`。
- `--repeat <count>`: 実行を繰り返す回数（平均化のため）。デフォルトは `500`。
- `--format <mode>`: 結果の出力形式（例: `cli`, `graph`）。
