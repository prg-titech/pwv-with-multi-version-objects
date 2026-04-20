# PWV with Multi-Version Objects

このリポジトリは現在再設計中です。

## ディレクトリ構成

- `archive/mvo-compiler-poc/`
  - 以前の proof-of-concept 実装です。
  - ユーザ定義のバージョン付きクラスを対象にした AST 変換コンパイラです。
  - 今後のコンパイラ生成、wrapper、テスト、ベンチマークの参照資料として残します。

- `work-in-progress/`
  - 新しい実装領域です。
  - まずは複数版モジュールを明示的に扱う logical module program 生成から作ります。
  - 最初の対象は、通常の import で読み込まれた複数版 module object を束ね、
    `a.member(version)` でアクセスできるようにすることです。

## 現在の作業対象

現在の WIP は module-family program 生成です。設計メモは以下です。

- `work-in-progress/docs/module-family-program.md`

WIP 側のテストは以下で実行します。

```bash
pytest
```

トップレベルのプロジェクト設定は `work-in-progress/` を向いています。
そのため、archive した旧 PoC を直接実行する場合は、別途 Python path や
pytest 設定を指定する必要があります。
