import os
import shutil
import subprocess
import sys
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parent
WIP_ROOT = TEST_ROOT.parent
GENERATED_DIR_NAME = "generated"


def setup_module():
    for generated_dir in (TEST_ROOT / "targets").glob(f"*/{GENERATED_DIR_NAME}"):
        shutil.rmtree(generated_dir)


def test_function_and_value_members_output():
    assert_target_output("function_and_value_members")
    generated_text = generated_program_text("function_and_value_members")
    assert "def field(version=None):" in generated_text
    assert "_field_current_version" in generated_text


def test_renamed_member_mapping_output():
    assert_target_output("renamed_member_mapping")


def test_class_dispatch_output():
    assert_target_output("class_dispatch")
    assert_generated_class_uses_embedded_method_sets("class_dispatch", "Test")
    generated_text = generated_program_text("class_dispatch")
    assert "def display(self):" in generated_text
    assert "def super_log(self, *args, **kwargs):" in generated_text


def test_class_sync_output():
    assert_target_output("class_sync")
    assert_generated_class_uses_embedded_method_sets("class_sync", "Point")
    generated_text = generated_program_text("class_sync")
    assert "@staticmethod\n    def sync_point_from_v1_to_v2" in generated_text
    assert "def get_cartesian(self):" in generated_text


def assert_target_output(target_name: str) -> None:
    actual = run_target_module(f"targets.{target_name}.program")
    expected = (
        TEST_ROOT / "targets" / target_name / "expected_output.txt"
    ).read_text(encoding="utf-8")

    assert normalize_output(actual) == normalize_output(expected)
    generated_program = generated_program_path(target_name)
    assert generated_program.exists()
    generated_text = generated_program.read_text(encoding="utf-8")
    assert "from mv" not in generated_text
    assert "import mv" not in generated_text
    assert "import inspect" not in generated_text
    assert "inspect.signature" not in generated_text
    assert "getattr_static" not in generated_text


def assert_generated_class_uses_embedded_method_sets(
    target_name: str,
    class_name: str,
) -> None:
    generated_text = generated_program_text(target_name)

    assert f"class {class_name}:" in generated_text
    assert "class _V1_Impl(object):" in generated_text
    assert "class _V2_Impl(object):" in generated_text
    assert f"_{class_name.upper()}_VERSION_INSTANCES_SINGLETON" in generated_text
    assert f"_{class_name.lower()}_current_state" in generated_text
    assert f"_{class_name.lower()}_switch_to_version" in generated_text
    assert f"].{class_name}." not in generated_text
    assert "def __getattr__" not in generated_text
    assert "def __setattr__" not in generated_text
    assert "object.__setattr__(self, '_state'" not in generated_text


def generated_program_path(target_name: str) -> Path:
    return TEST_ROOT / "targets" / target_name / "generated" / "package.py"


def generated_program_text(target_name: str) -> str:
    return generated_program_path(target_name).read_text(encoding="utf-8")


def run_target_module(module_name: str) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(WIP_ROOT / "src"),
            str(TEST_ROOT),
            env.get("PYTHONPATH", ""),
        ]
    )

    result = subprocess.run(
        [sys.executable, "-m", module_name],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout


def normalize_output(text: str) -> str:
    return text.strip().replace("\r\n", "\n")
