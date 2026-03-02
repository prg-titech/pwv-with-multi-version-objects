import os
import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.old_access_profile.cli import load_events, summarize_events
from mvo_compiler.mvo_compiler import compile

def test_profile_runtime_logs_method_access(tmp_path: Path):
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    log_path = tmp_path / "access_events.jsonl"
    source_dir.mkdir()

    (source_dir / "main.py").write_text(
        textwrap.dedent(
            """
            class Example__1__:
                def ping(self):
                    print("v1")

            class Example__2__:
                def ping(self):
                    print("v2")

            def main():
                example = Example()
                example.ping()

            if __name__ == "__main__":
                main()
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    compile(source_dir, output_dir)

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(output_dir.resolve()), str((PROJECT_ROOT / "src").resolve())])
    env["MVO_ACCESS_PROFILE_LOG"] = str(log_path)
    result = subprocess.run(
        [sys.executable, str((output_dir / "main.py").resolve())],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )

    events = load_events(log_path)
    assert result.stdout.strip() == "v1"
    assert len(events) == 1
    assert events[0]["class_name"] == "Example"
    assert events[0]["access_kind"] == "method_call"
    assert events[0]["member_name"] == "ping"
    assert events[0]["resolved_version"] == 1
    assert events[0]["latest_version"] == 2
    assert events[0]["callsite_function"] == "main"

def test_summarize_events_counts_old_hotspots(tmp_path: Path):
    callsite_file = str((tmp_path / "main.py").resolve())
    events = [
        {
            "class_name": "Example",
            "access_kind": "method_call",
            "member_name": "ping",
            "resolved_version": 1,
            "latest_version": 2,
            "callsite_file": callsite_file,
            "callsite_line": 10,
            "callsite_function": "main",
        },
        {
            "class_name": "Example",
            "access_kind": "method_call",
            "member_name": "ping",
            "resolved_version": 1,
            "latest_version": 2,
            "callsite_file": callsite_file,
            "callsite_line": 10,
            "callsite_function": "main",
        },
        {
            "class_name": "Example",
            "access_kind": "method_call",
            "member_name": "ping",
            "resolved_version": 2,
            "latest_version": 2,
            "callsite_file": callsite_file,
            "callsite_line": 12,
            "callsite_function": "main",
        },
    ]

    summary = summarize_events(events, version_map={}, top_n=5, base_dir=tmp_path)

    assert summary["total_access_count"] == 3
    assert summary["old_access_count"] == 2
    assert summary["old_access_unique_callsite_count"] == 1
    assert summary["hotspots"] == [
        {
            "callsite_file": "main.py",
            "callsite_line": 10,
            "callsite_function": "main",
            "old_access_count": 2,
        }
    ]
