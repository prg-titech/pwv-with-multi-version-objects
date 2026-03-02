import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def test_tetris_playable_profile_interactive_quit(tmp_path: Path):
    output_root = tmp_path / "runs"
    target_dir = PROJECT_ROOT / "experiments" / "old_access_profile" / "targets"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "experiments.old_access_profile.cli",
            str(target_dir),
            "--entry-file",
            "tetris/playable_main.py",
            "--interactive",
            "--output-root",
            str(output_root),
        ],
        input="q\n",
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
    )

    stdout = result.stdout.replace("\r\n", "\n")
    assert "old_access_count:" in stdout
    assert "score=0" in stdout
    assert "sync v1->v2: 0" in stdout
    run_dir = Path(stdout.strip().splitlines()[-1])
    summary_path = run_dir / "summary.json"
    assert summary_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["interactive"] is True
    assert summary["old_access_count"] > 0
