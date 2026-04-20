from __future__ import annotations

from pathlib import Path
from typing import Any

import mv


def compile_and_load_package(program_file: str, **compile_options: Any):
    generated_path = Path(program_file).with_name("generated") / "package.py"
    mv.compile_module_family_program(
        output_path=generated_path,
        **compile_options,
    )
    return mv.load_module_program(generated_path, "package")
