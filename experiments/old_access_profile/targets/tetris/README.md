# tetris

このフォルダは、`EventBus` を利用するテトリスアプリケーション本体を置く場所です。

- `main.py`
  固定シナリオ実行の共有エントリです。既定では `original/game/` を使います。
- `playable_main.py`
  簡易プレイアブル実行の共有エントリです。既定では `original/game/` を使います。
- `original/`
  更新前の基準実装です。中には `game/` だけを置きます。
- `updates/`
  更新途中の版を置くための場所です。各 `updateN/` の中には `game/` だけを置く想定です。
