# 旧版アクセスプロファイル

`python -m experiments.old_access_profile.cli <target_dir>` で、MVO アプリをコンパイル・実行し、`access_events.jsonl` と `summary.json` を出力します。

既定のコンパイル戦略は `latest` です。必要なら `--strategy continuity` を明示して切り替えます。

例:
- `python -m experiments.old_access_profile.cli experiments/old_access_profile/targets --entry-file tetris/main.py`
- `python -m experiments.old_access_profile.cli experiments/old_access_profile/targets --entry-file tetris/playable_main.py --interactive`
- `python -m experiments.old_access_profile.cli experiments/old_access_profile/targets --entry-file tetris/main.py --runtime-env MVO_TETRIS_STAGE=updates/update1`

任意オプション:
- `--version-map <json>`: クラスごとの latest version を上書きします。
- `--compare-to <summary.json>`: 前回との差分を表示します。
- `--output-root <dir>`: 実行結果の保存先を変更します。
- `--interactive`: 標準入力を引き継ぎ、対話実行します。終了後にサマリを表示します。
- `--runtime-env <KEY=VALUE>`: 実行時環境変数を追加します。更新段階の切替に使えます。

出力物:
- `access_events.jsonl`: 行指向の生ログ
- `stdout.txt`: 対象アプリの標準出力
- `summary.json`: 集計済みサマリ

対象アプリは `experiments/old_access_profile/targets/` 配下に置く想定です。現在は `EventBus/` と `tetris/` をまとめて 1 つの target root としてコンパイルします。
