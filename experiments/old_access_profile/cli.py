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
DEFAULT_ENTRY_FILE = "main.py"
DEFAULT_TOP_N = 10
DEFAULT_RUNS_ROOT = PROJECT_ROOT / "experiments" / "old_access_profile" / "runs"

def main() -> None:
    parser = argparse.ArgumentParser(description="旧版アクセスのプロファイルを取得して集計します。")
    parser.add_argument("target_dir", help="MVO アプリケーションのソースディレクトリ。")
    parser.add_argument("--strategy", choices=list(VERSION_SELECTION_STRATEGIES), default=VERSION_SELECTION_LATEST)
    parser.add_argument("--entry-file", default=DEFAULT_ENTRY_FILE, help="コンパイル後ディレクトリ内の実行対象ファイル名。")
    parser.add_argument("--output-root", default=str(DEFAULT_RUNS_ROOT), help="プロファイル結果の出力先ルート。")
    parser.add_argument("--version-map", help="クラスごとの latest version を上書きする JSON ファイル。")
    parser.add_argument("--compare-to", help="前回実行の summary.json。差分表示に使います。")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="表示する hotspot 件数。")
    parser.add_argument("--interactive", action="store_true", help="標準入力を引き継いで対話実行します。")
    parser.add_argument("--runtime-env", action="append", default=[], metavar="KEY=VALUE", help="対象アプリに渡す環境変数です。")
    args = parser.parse_args()

    target_dir = Path(args.target_dir).resolve()
    output_root = Path(args.output_root).resolve()
    version_map = _load_version_map(Path(args.version_map).resolve()) if args.version_map else {}
    compare_to = Path(args.compare_to).resolve() if args.compare_to else None

    run_dir = profile_target(
        target_dir=target_dir,
        output_root=output_root,
        strategy=args.strategy,
        entry_file=args.entry_file,
        version_map=version_map,
        compare_to=compare_to,
        top_n=args.top,
        interactive=args.interactive,
        runtime_env=_parse_runtime_env(args.runtime_env),
    )
    print(run_dir)

def profile_target(
    *,
    target_dir: Path,
    output_root: Path,
    strategy: str,
    entry_file: str,
    version_map: dict[str, int],
    compare_to: Path | None,
    top_n: int,
    interactive: bool,
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
        interactive=interactive,
        runtime_env=runtime_env,
    )
    if stdout is None:
        stdout_path.write_text("interactive mode: stdout was streamed directly to the terminal.\n", encoding="utf-8")
    else:
        stdout_path.write_text(stdout, encoding="utf-8")

    events = load_events(log_path)
    previous_summary = _load_json(compare_to) if compare_to else None
    summary = summarize_events(
        events,
        version_map=version_map,
        top_n=top_n,
        base_dir=transpiled_dir,
        previous_summary=previous_summary,
    )
    summary["target_dir"] = str(target_dir)
    summary["strategy"] = strategy
    summary["entry_file"] = entry_file
    summary["interactive"] = interactive
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
    version_map: dict[str, int],
    top_n: int,
    base_dir: Path,
    previous_summary: dict | None = None,
) -> dict:
    old_events = []
    hotspot_counter: Counter[tuple[str, int, str]] = Counter()

    for event in events:
        latest_version = version_map.get(event["class_name"], event["latest_version"])
        if event["resolved_version"] >= latest_version:
            continue
        old_events.append(event)
        hotspot_counter[(event["callsite_file"], event["callsite_line"], event["callsite_function"])] += 1

    hotspots = []
    for (file_name, line_no, function_name), count in hotspot_counter.most_common(top_n):
        hotspots.append({
            "callsite_file": _display_path(file_name, base_dir),
            "callsite_line": line_no,
            "callsite_function": function_name,
            "old_access_count": count,
        })

    summary = {
        "total_access_count": len(events),
        "old_access_count": len(old_events),
        "old_access_unique_callsite_count": len(hotspot_counter),
        "hotspots": hotspots,
    }
    if previous_summary is not None:
        summary["diff_from_previous"] = {
            "old_access_count": len(old_events) - int(previous_summary.get("old_access_count", 0)),
            "old_access_unique_callsite_count": len(hotspot_counter) - int(previous_summary.get("old_access_unique_callsite_count", 0)),
        }
    return summary

def format_summary(summary: dict, *, top_n: int) -> str:
    lines = [
        f"old_access_count: {summary['old_access_count']}",
        f"old_access_unique_callsite_count: {summary['old_access_unique_callsite_count']}",
        f"total_access_count: {summary['total_access_count']}",
    ]
    diff = summary.get("diff_from_previous")
    if diff:
        lines.append(f"delta_old_access_count: {diff['old_access_count']:+d}")
        lines.append(f"delta_old_access_unique_callsite_count: {diff['old_access_unique_callsite_count']:+d}")

    lines.append(f"hotspots_top_{top_n}:")
    if not summary["hotspots"]:
        lines.append("  (none)")
    else:
        for hotspot in summary["hotspots"]:
            lines.append(
                f"  {hotspot['old_access_count']:>5}  {hotspot['callsite_file']}:{hotspot['callsite_line']}  {hotspot['callsite_function']}"
            )
    return "\n".join(lines)

def _execute_with_profile(
    output_dir: Path,
    entry_file: str,
    log_path: Path,
    *,
    interactive: bool,
    runtime_env: dict[str, str],
) -> str | None:
    entry_file_path = output_dir / entry_file
    env = os.environ.copy()
    env["PYTHONPATH"] = _extend_pythonpath(output_dir, env.get("PYTHONPATH"))
    env[PROFILE_LOG_ENV_VAR] = str(log_path)
    env.update(runtime_env)
    if interactive:
        subprocess.run(
            [sys.executable, str(entry_file_path.resolve())],
            check=True,
            env=env,
        )
        return None
    result = subprocess.run(
        [sys.executable, str(entry_file_path.resolve())],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
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
    file_path = Path(file_name).resolve()
    for candidate in (base_dir.resolve(), PROJECT_ROOT):
        try:
            return str(file_path.relative_to(candidate))
        except ValueError:
            continue
    return str(file_path)

def _load_version_map(path: Path) -> dict[str, int]:
    data = _load_json(path)
    return {class_name: int(version) for class_name, version in data.items()}


def _parse_runtime_env(items: list[str]) -> dict[str, str]:
    env = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid runtime env: {item}")
        key, value = item.split("=", 1)
        env[key] = value
    return env

def _load_json(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    main()
