"""function/value member の実行対象プログラム。

top-level function は `package.describe(version, *args)` として呼ぶ。
値は `package.field(version)` として取得する。
version を省略すると直前の version を継続する。

期待する出力:
value-v1
value-v2
value-v2
function-v1:sample
function-v2:sample
"""

from __future__ import annotations

from . import package_v1, package_v2
from ..support import compile_and_load_package


def main() -> None:
    package = compile_and_load_package(
        __file__,
        versions={1: package_v1, 2: package_v2},
    )

    print(package.field())
    print(package.field(2))
    print(package.field())
    print(package.describe(1, "sample"))
    print(package.describe(2, "sample"))


if __name__ == "__main__":
    main()
