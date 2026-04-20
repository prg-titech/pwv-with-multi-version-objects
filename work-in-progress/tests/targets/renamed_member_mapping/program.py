"""version 間で名前が違う member の実行対象プログラム。

名前が異なる member は module 上でも別の公開名として扱う。

期待する出力:
mapped-field-v1
mapped-field-v2
mapped-method-v1:x
mapped-method-v2:x
"""

from __future__ import annotations

from . import package_v1, package_v2
from ..support import compile_and_load_package


def main() -> None:
    package = compile_and_load_package(
        __file__,
        versions={1: package_v1, 2: package_v2},
        member_map={
            "field": {1: "field", 2: "renamed_field"},
            "method": {1: "method", 2: "renamed_method"},
        },
    )

    print(package.field(1))
    print(package.renamed_field(2))
    print(package.method(1, "x"))
    print(package.renamed_method(2, "x"))


if __name__ == "__main__":
    main()
