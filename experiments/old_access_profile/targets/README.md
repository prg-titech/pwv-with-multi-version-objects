# targets 構成

このディレクトリは、ポスター実験で使うアプリケーション一式をまとめて置くための target root です。

- `EventBus/`
  `EventBus` の配布物を模した共通ライブラリです。`event_bus.py` に v1 と v2 を定義し、`EventBus_sync.py` に状態変換を置いています。
- `tetris/original/`
  更新前のテトリス本体です。固定シナリオ実行の `main.py` と、簡易プレイアブル実行の `playable_main.py` があります。
- `tetris/updates/`
  更新途中の版を並べるための作業場所です。`original` を複製して段階的に修正していく想定です。

EventBus の非互換性は次の 2 点です。

- v1 は `on`, `off`, `emit` を持ち、内部状態は `event -> callbacks` です。
- v2 は `subscribe`, `unsubscribe`, `publish` を持ち、内部状態は `event -> subscriber records` と `token index` です。

テトリス側では、`tetris/original/game/` 配下の各モジュールが `EventBus` を使います。更新前の `original` では、`renderer`、`audio`、`hud`、`score`、`stats` がすべて v1 API に依存しています。
