# experiments

このディレクトリには、論文・ポスター向けの検証用実験を置きます。

現在の主な内容:

- `old_access_profile/`
  MVO アプリを実行し、旧版 API へのアクセス回数とホットスポットを集計する実験です。

## old_access_profile

この実験は、MVO アプリをコンパイル・実行し、旧版 API へのアクセス回数とアクセス箇所を集計するためのものです。

実行コマンド:

- `python -m experiments.old_access_profile.cli`

既定の version selection strategy は `latest` です。

例:

- `python -m experiments.old_access_profile.cli`
- `python -m experiments.old_access_profile.cli --playable`
- `python -m experiments.old_access_profile.cli --runtime-env MVO_TETRIS_STAGE=updates/update5`

任意オプション:

- `--strategy continuity`: version selection を切り替える
- `--playable`: `tetris/main.py` をプレイ可能モードで実行する
- `--runtime-env <KEY=VALUE>`: 更新段階切替などの環境変数を渡す

出力物:

- `access_events.jsonl`: 行指向の生ログ
- `stdout.txt`: 対象アプリの標準出力
- `summary.json`: 集計済みサマリ

## Target Layout

対象アプリは `experiments/old_access_profile/targets/` 配下に置きます。

- `EventBus/`
  実験用の共通ライブラリです。`event_bus.py` に v1 と v2 の `EventBus` 定義、`EventBus_sync.py` に状態変換を置きます。
- `tetris/`
  `EventBus` を利用するテトリス本体です。エントリは `main.py` です。
- `tetris/original/game/`
  更新前の基準実装です。
- `tetris/updates/updateN/game/`
  更新途中の版です。`MVO_TETRIS_STAGE=updates/updateN` で切り替えます。

既定では固定されたデモシナリオを実行します。`--playable` を付けたときだけプレイ可能モードで動きます。

EventBus の非互換性:

- v1 は `on`, `off`, `emit` を使う
- v2 は `subscribe`, `unsubscribe`, `publish` を使う
- v2 は token と priority を前提にするため、listener 側の移行では token 管理も必要になる

更新前の `tetris/original/game/` では、`renderer`、`audio`、`hud`、`score`、`stats` が v1 API に依存しています。

## Documents

- [TETRIS_MIGRATION_HISTORY.md](/Users/kasuyasatsuki/Research/pwv-with-multi-version-objects/experiments/TETRIS_MIGRATION_HISTORY.md)
  `update1` から `update5` までの移行内容と `old_access_count` の推移。
