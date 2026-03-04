import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mvo_compiler.mvo_compiler import compile
from mvo_compiler.util.constants import VERSION_SELECTION_LATEST, VERSION_SELECTION_STRATEGIES

PROFILE_LOG_ENV_VAR = "MVO_ACCESS_PROFILE_LOG"
TETRIS_MODE_ENV_VAR = "MVO_TETRIS_MODE"
DEFAULT_ENTRY_FILE = "tetris/main.py"
DEFAULT_TOP_N = 10
DEFAULT_TARGET_DIR = PROJECT_ROOT / "experiments" / "old_access_profile" / "targets"
DEFAULT_RUNS_ROOT = PROJECT_ROOT / "experiments" / "old_access_profile" / "runs"

def main() -> None:
    parser = argparse.ArgumentParser(description="旧版アクセスのプロファイルを取得して集計します。")
    parser.add_argument("--strategy", choices=list(VERSION_SELECTION_STRATEGIES), default=VERSION_SELECTION_LATEST)
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="表示する hotspot 件数。")
    parser.add_argument("--playable", action="store_true", help="Tetris をプレイ可能モードで実行します。")
    parser.add_argument("--runtime-env", action="append", default=[], metavar="KEY=VALUE", help="対象アプリに渡す環境変数です。")
    args = parser.parse_args()

    run_dir = profile_target(
        target_dir=DEFAULT_TARGET_DIR.resolve(),
        output_root=DEFAULT_RUNS_ROOT.resolve(),
        strategy=args.strategy,
        entry_file=DEFAULT_ENTRY_FILE,
        top_n=args.top,
        playable=args.playable,
        runtime_env=_parse_runtime_env(args.runtime_env),
    )
    print(run_dir)

def profile_target(
    *,
    target_dir: Path,
    output_root: Path,
    strategy: str,
    entry_file: str,
    top_n: int,
    playable: bool,
    runtime_env: dict[str, str],
) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = output_root / timestamp
    transpiled_dir = run_dir / "transpiled"
    log_path = run_dir / "access_events.jsonl"
    stdout_path = run_dir / "stdout.txt"
    summary_path = run_dir / "summary.json"

    compile(target_dir, transpiled_dir, version_selection_strategy=strategy)
    stdout = _execute_with_profile(
        transpiled_dir,
        entry_file,
        log_path,
        playable=playable,
        runtime_env=runtime_env,
    )
    if stdout is None:
        stdout_path.write_text("playable mode: stdout was streamed directly to the terminal.\n", encoding="utf-8")
    else:
        stdout_path.write_text(stdout, encoding="utf-8")

    events = load_events(log_path)
    summary = summarize_events(
        events,
        top_n=top_n,
        base_dir=transpiled_dir,
    )
    summary["target_dir"] = str(target_dir)
    summary["strategy"] = strategy
    summary["entry_file"] = entry_file
    summary["playable"] = playable
    summary["runtime_env"] = runtime_env
    summary["artifacts"] = {
        "run_dir": str(run_dir),
        "transpiled_dir": str(transpiled_dir),
        "log_path": str(log_path),
        "stdout_path": str(stdout_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")

    print(format_summary(summary, top_n=top_n))
    return run_dir

def load_events(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    events = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events

def summarize_events(
    events: list[dict],
    *,
    top_n: int,
    base_dir: Path,
) -> dict:
    old_events = []
    hotspot_counter: Counter[tuple[str, int, str, str, str]] = Counter()

    for event in events:
        latest_version = event["latest_version"]
        if event["resolved_version"] >= latest_version:
            continue
        old_events.append(event)
        hotspot_counter[(
            event["callsite_file"],
            event["callsite_line"],
            event["access_kind"],
            event["member_name"],
            event.get("callsite_source_line", ""),
        )] += 1

    hotspots = []
    for (file_name, line_no, access_kind, member_name, source_line), count in hotspot_counter.most_common(top_n):
        hotspots.append({
            "callsite_file": _display_path(file_name, base_dir),
            "callsite_line": line_no,
            "access": _format_access_label(access_kind, member_name, source_line),
            "access_kind": access_kind,
            "member_name": member_name,
            "callsite_source_line": source_line,
            "old_access_count": count,
        })

    summary = {
        "total_access_count": len(events),
        "old_access_count": len(old_events),
        "old_access_unique_callsite_count": len(hotspot_counter),
        "hotspots": hotspots,
    }
    return summary

def format_summary(summary: dict, *, top_n: int) -> str:
    lines = [
        f"old_access_count: {summary['old_access_count']}",
        f"old_access_unique_callsite_count: {summary['old_access_unique_callsite_count']}",
        f"total_access_count: {summary['total_access_count']}",
    ]
    lines.append(f"hotspots_top_{top_n}:")
    if not summary["hotspots"]:
        lines.append(" (none)")
    else:
        for hotspot in summary["hotspots"]:
            lines.append(
                f" {hotspot['old_access_count']:>3}  {hotspot['callsite_file']}:{hotspot['callsite_line']}  {hotspot['access']}"
            )
    return "\n".join(lines)


def _format_access_label(access_kind: str, member_name: str, source_line: str) -> str:
    if source_line:
        return source_line
    if access_kind == "method_call":
        return f"*.{member_name}(...)"
    if access_kind == "attribute_read":
        return f"*.{member_name}"
    if access_kind == "attribute_write":
        return f"*.{member_name} = ..."
    return member_name

def _execute_with_profile(
    output_dir: Path,
    entry_file: str,
    log_path: Path,
    *,
    playable: bool,
    runtime_env: dict[str, str],
) -> str | None:
    entry_file_path = output_dir / entry_file
    env = os.environ.copy()
    env["PYTHONPATH"] = _extend_pythonpath(output_dir, env.get("PYTHONPATH"))
    env[PROFILE_LOG_ENV_VAR] = str(log_path)
    env.update(runtime_env)
    if playable:
        env[TETRIS_MODE_ENV_VAR] = "playable"
        subprocess.run(
            [sys.executable, str(entry_file_path.resolve())],
            check=True,
            text=True,
            env=env,
        )
        return None
    result = subprocess.run(
        [sys.executable, str(entry_file_path.resolve())],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(_format_subprocess_failure(entry_file_path, result))
    return result.stdout

def _extend_pythonpath(output_dir: Path, existing: str | None) -> str:
    entries = [
        str(output_dir.resolve()),
        str((PROJECT_ROOT / "src").resolve()),
        str(PROJECT_ROOT.resolve()),
    ]
    if existing:
        entries.append(existing)
    return os.pathsep.join(entries)

def _display_path(file_name: str, base_dir: Path) -> str:
    return Path(file_name).name

def _parse_runtime_env(items: list[str]) -> dict[str, str]:
    env = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid runtime env: {item}")
        key, value = item.split("=", 1)
        env[key] = value
    return env

def _format_subprocess_failure(entry_file_path: Path, result: subprocess.CompletedProcess[str]) -> str:
    parts = [
        f"Execution failed for {entry_file_path} with exit code {result.returncode}.",
    ]
    if result.stdout:
        parts.append("stdout:")
        parts.append(result.stdout.rstrip())
    if result.stderr:
        parts.append("stderr:")
        parts.append(result.stderr.rstrip())
    return "\n".join(parts)

if __name__ == "__main__":
    main()
