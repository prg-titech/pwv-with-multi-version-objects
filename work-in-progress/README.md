# 作業中の新実装

このディレクトリには、モジュールレベルの複数版管理の新設計を置きます。

現在の中心は、複数版 module から単一の logical module program を生成する処理です。

- version ごとの module object は通常の Python import で読み込みます。
- `mv.compile_module_family_program(...)` で logical module program を生成します。
- `mv.load_module_program(...)` で生成済み program を plain module として読み込みます。
- 下流コードは `a.member(version)` の形で明示的に版を指定します。

設計の詳細と、この段階で扱わない範囲は
`docs/module-family-program.md` を参照してください。

## テスト構成

- `tests/targets/`
  - テスト対象プログラムを置きます。
  - 対象プログラム側には、その module が期待する挙動を docstring として書きます。
  - 期待 stdout は target ごとの `expected_output.txt` に置きます。
  - 例: `module_family_basic/program.py`, `module_family_policy/program.py`,
    `module_family_mapping/program.py`
- `tests/test_*.py`
  - 生成 program と実行結果の検証コードを置きます。
  - 対象プログラムを実行し、stdout を capture して期待出力と比較します。
