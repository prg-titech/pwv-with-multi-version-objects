import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mvo_compiler.mvo_compiler import compile, execute

def test_tetris_original_target_runs(tmp_path: Path):
    target_dir = PROJECT_ROOT / "experiments" / "old_access_profile" / "targets"

    compile(target_dir, tmp_path)
    output = execute("tetris/main.py", tmp_path)

    expected_output = "\n".join([
        "turn=1 piece=O x=0",
        "render lock O at (0,4)",
        "......",
        "......",
        "......",
        "......",
        "##....",
        "##....",
        "turn=2 piece=O x=2",
        "render lock O at (2,4)",
        "......",
        "......",
        "......",
        "......",
        "####..",
        "####..",
        "turn=3 piece=O x=4",
        "render lock O at (4,4)",
        "......",
        "......",
        "......",
        "......",
        "######",
        "######",
        "render clear lines=2",
        "......",
        "......",
        "......",
        "......",
        "......",
        "......",
        "audio clear lines=2",
        "hud total_lines=2",
        "turn=4 piece=I x=3",
        "render lock I at (3,2)",
        "......",
        "......",
        "...#..",
        "...#..",
        "...#..",
        "...#..",
        "audio finish",
        "hud finished pieces=4 lines=2",
        "score=300",
        "locks=4 lines=2",
        "sync v1->v2: 0",
        "sync v2->v1: 0",
    ])

    assert output.strip().replace("\r\n", "\n") == expected_output
