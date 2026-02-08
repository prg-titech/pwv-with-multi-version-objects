# PWV with Multi-Version Objects

## 概要

本プロジェクトは、論文で提案する「PWV with Multi-Version Objects (MVO)」の PoC トランスパイラです。Python の AST を解析し、バージョン付きクラス群を統合クラスに変換して実行します。

## 仕組み

1. Parse: 入力ディレクトリ配下の .py を AST 化し、_sync.py を同期モジュールとして分類します。 .json も読み込みます。
2. Transform:
- SymbolTable 構築: クラス/メソッド/継承関係を収集します。
- UnifiedClassBuilder: バージョン付きクラスを統合クラスへ変換します（State パターン）。
3. Generate: AST を Python ソースに戻し、出力ディレクトリに書き出します。
4. Execute: 生成された main.py を実行します（main.py 経由の場合）。

## 要件

- Python 3.12 以上
- uv: 高速なパッケージインストーラ/リゾルバ

## セットアップ

```bash
# Python バージョン固定 (.python-version を作成)
uv python pin 3.12

# 依存関係インストール (.venv と uv.lock が無ければ作成)
uv sync
```

uv sync の内容
- .venv を作成
- 依存関係をインストール
- プロジェクトを editable でインストール（src/mvo_compiler を import 可能にする）

### 仮想環境の有効化

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\activate

# deactivate
deactivate
```

## 実行方法

### 手動実行

```bash
# 例: basic_cases/basic_01 を実行
python main.py basic_cases/basic_01

# デバッグログを有効化
python main.py basic_cases/basic_01 --debug

# バージョン選択戦略を指定
python main.py basic_cases/basic_01 --strategy latest
```

- target_dir は test/resources/samples からの相対パスです。
- strategy は continuity | latest を選択します。

## 入力形式と暗黙ルール

### 1. 入力ディレクトリ

compile() に渡すディレクトリ配下を再帰的にスキャンします。
- **/*.py はソースファイル
- **/*_sync.py は同期モジュール
- **/*.json は互換性(属性)定義

### 2. バージョン付きクラス

- 同一ベース名のバージョンは同一ファイルに定義します。
- クラス名は `<BaseName>__<version>__` 形式で、version は整数です。
- クラス定義はトップレベルメソッドのみを対象にします。
- クラス属性（AnnAssign/Assign）は無視されます。
- 内部クラスは未対応です。

**例**
```python
class Point__1__:
    def __init__(self, x: int):
        self.x = x

class Point__2__:
    def __init__(self, r: float):
        self.r = r
```

### 3. 継承

- バージョン付きクラスは通常クラス/バージョン付きクラスを継承できます。
- `Foo__2__` のようにバージョン付きクラスを継承した場合、バージョン情報も継承関係として記録されます。

### 4. 同期モジュール (sync_modules)

- ファイル名は `<BaseName>_sync.py` です（例: Point_sync.py）。
- 位置は入力ディレクトリ配下ならどこでも構いません。
- 同期関数名は `_?sync_from_v<from>_to_v<to>` 形式です。先頭の `_` は任意です。
- 同期関数の引数は 1 つ（wrapper オブジェクト）です。
- 同期モジュール内の import 文は統合クラスの先頭へ移されます。

**例**
```python
def _sync_from_v1_to_v2(wrapper_obj):
    wrapper_obj._v2 = "Version 2"
    del wrapper_obj._v1
```

### 5. 互換性(属性)定義 JSON

入力ディレクトリ配下の任意の .json を読み込みます。

スキーマ
```json
{
  "<BaseName>": {
    "<version>": ["attr1", "attr2"]
  }
}
```

- `<version>` は整数の文字列です。

### 6. エントリポイント

main.py 経由で実行する場合、入力ディレクトリ直下に main.py が存在することを想定します。

## テスト

- 入力サンプル: test/resources/samples/
- 期待出力: test/resources/expected_output/

### テストの実行

```bash
# 全テスト
pytest

# 特定のテストのみ
pytest --target_dir=basic_cases/basic_01

# デバッグログ付き
pytest --debug --target_dir=basic_cases/basic_01
```

## ディレクトリ構成

```
.
├── main.py
├── pyproject.toml
├── src/
│   └── mvo_compiler/
│       ├── mvo_compiler.py
│       ├── scanner.py
│       ├── transformer.py
│       ├── builder/
│       ├── symbol_table/
│       ├── util/
│       └── templates/
└── test/
    ├── conftest.py
    ├── test_create.py
    ├── test_transformer.py
    └── resources/
        ├── samples/
        └── expected_output/
```
