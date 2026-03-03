# Tetris EventBus Migration History

`experiments/old_access_profile/targets/tetris/original/game/` から `updates/update5/game/` までの EventBus v1 依存削減の過程をまとめた記録です。

## Goal

- `EventBus` の v1 API 依存を段階的に v2 API へ移行する
- 各段階で profiler を実行し、`old_access_count` の減少を確認する
- 後から `updateN` ごとの差分を追いやすくする

前提:

- v1 API: `on`, `off`, `emit`
- v2 API: `subscribe`, `unsubscribe`, `publish`
- 実行切替: `MVO_TETRIS_STAGE=updates/updateN`

## Result

`update5` 実行時:

- `old_access_count: 12`
- `old_access_unique_callsite_count: 8`
- `total_access_count: 30`

残っている主な旧 API 呼び出し:

- `audio.py`: `on` / `off`
- `stats.py`: `on` / `off`
- `score.py`: `on` / `off`
- `engine.py`: `emit("line_cleared", ...)`, `emit("game_finished", ...)`

## Updates

### update1

対象:

- `engine.py`

変更:

- `self.bus.emit("turn_started", ...)` を `self.bus.publish("turn_started", ...)` に変更

意図:

- 送信側イベントを 1 箇所だけ v2 API に切り替え、影響範囲を小さく確認する

### update2

対象:

- `engine.py`

変更:

- `self.bus.emit("piece_locked", ...)` を `self.bus.publish("piece_locked", ...)` に変更

意図:

- `engine.py` のイベント送信を段階的に v2 API に寄せる

### update3

対象:

- `hud.py`

変更:

- `bus.on(event_name, callback)` を `bus.subscribe(event_name, callback)` に変更
- `_subscriptions` を `(event_name, callback)` から `(event_name, callback, token)` に変更
- `subscribe()` の戻り値 token を保持するように変更
- uninstall 側はまだ `off(event_name, callback)` のまま

意図:

- listener 側の移行に必要な token 管理を先に入れる

### update4

対象:

- `hud.py`

変更:

- `bus.off(event_name, callback)` を `bus.unsubscribe(token)` に変更

意図:

- `hud.py` の登録・解除をともに v2 API ベースへ移行完了させる

### update5

対象:

- `renderer.py`

変更:

- `bus.on(event_name, callback)` を `bus.subscribe(event_name, callback)` に変更
- `bus.off(event_name, callback)` を `bus.unsubscribe(token)` に変更
- `_subscriptions` を token 管理付きの構造へ変更

意図:

- `hud.py` で確認した移行パターンを別コンポーネントへ展開する

## Trend

- `engine.py` 側は `emit -> publish` をイベント単位で段階的に移行した
- listener 側は `on/off -> subscribe/unsubscribe` に加えて token 管理への内部構造変更が必要だった
- `update5` までで `old_access_count` は `12` まで減少した
- 以降は同じ移行パターンを `audio.py`, `stats.py`, `score.py`, `engine.py` の残件へ適用する作業が中心になる

## Command

```bash
python -m experiments.old_access_profile.cli \
  --runtime-env MVO_TETRIS_STAGE=updates/update5
```
