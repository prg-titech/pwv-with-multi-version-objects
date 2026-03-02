# updates

このフォルダには、`original` を複製して作る更新途中のテトリス実装を配置します。

想定する使い方:

- `original/game/` を `updates/update1/game/` のように複製する
- 一部のモジュールだけ EventBus v2 API に移行する
- profiler を再実行して、旧アクセス回数と旧アクセス箇所数の変化を見る

実行時の切替:

- 共有エントリは `tetris/main.py` と `tetris/playable_main.py` を使います。
- 既定では `original` を実行します。
- 更新途中の版を実行するときは `MVO_TETRIS_STAGE=updates/update1` のように stage を指定します。
