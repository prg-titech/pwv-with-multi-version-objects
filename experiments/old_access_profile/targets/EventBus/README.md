# EventBus

このフォルダは、外部配布ライブラリを模した `EventBus` の実装を置く場所です。

- `event_bus.py`
  v1 と v2 の `EventBus` 定義を含みます。
- `EventBus_sync.py`
  v1 表現と v2 表現のあいだを往復する state-to-state mapping を定義します。

非互換の要点:

- v1 は `on`, `off`, `emit` を使います。
- v2 は `subscribe`, `unsubscribe`, `publish` を使います。
- v2 は token と priority を前提にするため、v1 の内部状態のままではそのまま動きません。
