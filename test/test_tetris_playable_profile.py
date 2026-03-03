import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def test_tetris_playable_profile_quit(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.old_access_profile.cli",
            "--playable",
        ],
        input="q\n",
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
    assert "score=0" in stdout
    assert "sync v1->v2: 0" in stdout
    app_stdout = stdout_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert "playable mode: stdout was streamed directly to the terminal." in app_stdout
    assert summary["playable"] is True
    assert summary["old_access_count"] > 0
