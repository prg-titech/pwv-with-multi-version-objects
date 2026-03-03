import json
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
    assert events[0]["callsite_source_line"] == "example.ping()"

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
            "callsite_source_line": "example.ping()",
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
            "callsite_source_line": "example.ping()",
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
            "callsite_source_line": "example.ping()",
        },
    ]

    summary = summarize_events(events, top_n=5, base_dir=tmp_path)

    assert summary["total_access_count"] == 3
    assert summary["old_access_count"] == 2
    assert summary["old_access_unique_callsite_count"] == 1
    assert summary["hotspots"] == [
        {
            "callsite_file": "main.py",
            "callsite_line": 10,
            "access": "example.ping()",
            "access_kind": "method_call",
            "member_name": "ping",
            "callsite_source_line": "example.ping()",
            "old_access_count": 2,
        }
    ]


def test_profile_cli_runs_tetris_update_stage(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.old_access_profile.cli",
            "--runtime-env",
            "MVO_TETRIS_STAGE=updates/update1",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
    )

    stdout = result.stdout.replace("\r\n", "\n")
    assert "old_access_count:" in stdout

    run_dir = Path(stdout.strip().splitlines()[-1])
    summary_path = run_dir / "summary.json"
    stdout_path = run_dir / "stdout.txt"
    assert summary_path.exists()
    assert stdout_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    app_stdout = stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")

    assert summary["target_dir"] == str(PROJECT_ROOT / "experiments" / "old_access_profile" / "targets")
    assert summary["runtime_env"] == {"MVO_TETRIS_STAGE": "updates/update1"}
    assert summary["entry_file"] == "tetris/main.py"
    assert "score=300" in app_stdout
    assert "sync v1->v2:" in app_stdout
    assert "sync v2->v1:" in app_stdout


def test_compile_preserves_non_versioned_source_text(tmp_path: Path):
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()

    source_text = textwrap.dedent(
        """
        def run():

            # keep this blank line and comment
            print("hello")
        """
    ).lstrip()
    (source_dir / "plain.py").write_text(source_text, encoding="utf-8")

    compile(source_dir, output_dir)

    assert (output_dir / "plain.py").read_text(encoding="utf-8") == source_text
