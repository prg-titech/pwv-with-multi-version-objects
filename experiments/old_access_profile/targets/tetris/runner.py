import os
from importlib import import_module

STAGE_ENV_VAR = "MVO_TETRIS_STAGE"
DEFAULT_STAGE = "original"


def run_demo() -> None:
    _run(playable=False)


def run_playable() -> None:
    _run(playable=True)


def _run(*, playable: bool) -> None:
    stage = _get_stage()
    engine_module = import_module(f"tetris.{stage}.game.engine")
    event_bus_module = import_module(f"tetris.{stage}.game.event_bus")
    audio_module = import_module(f"tetris.{stage}.game.audio")
    hud_module = import_module(f"tetris.{stage}.game.hud")
    renderer_module = import_module(f"tetris.{stage}.game.renderer")
    score_module = import_module(f"tetris.{stage}.game.score")
    stats_module = import_module(f"tetris.{stage}.game.stats")

    bus = event_bus_module.EventBus()
    systems = [
        renderer_module.Renderer(),
        audio_module.Audio(),
        hud_module.Hud(),
        score_module.Score(),
        stats_module.Stats(),
    ]
    for system in systems:
        system.install(bus)

    engine = engine_module.TetrisEngine(bus)
    try:
        if playable:
            engine.run_playable()
        else:
            engine.run_demo()
    finally:
        for system in reversed(systems):
            system.uninstall(bus)

        print(f"score={systems[3].total_score}")
        print(f"locks={systems[4].lock_count} lines={systems[4].total_lines}")
        print(f"sync v1->v2: {bus._sync_v1_to_v2_count}")
        print(f"sync v2->v1: {bus._sync_v2_to_v1_count}")


def _get_stage() -> str:
    stage = os.environ.get(STAGE_ENV_VAR, DEFAULT_STAGE).strip().replace("\\", "/").strip("/")
    if not stage:
        return DEFAULT_STAGE
    if stage == "original":
        return stage
    if stage.startswith("updates/"):
        return stage.replace("/", ".")
    raise ValueError(f"Unsupported Tetris stage: {stage}")
