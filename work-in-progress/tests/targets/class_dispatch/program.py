"""class method dispatch の実行対象プログラム。

期待する出力:
type
package
Test
display-v1
log-v2
test-v2
super-v1:Hello:Alice
test-v1
"""

from __future__ import annotations

from . import package_v1, package_v2
from ..support import compile_and_load_package


def main() -> None:
    package = compile_and_load_package(
        __file__,
        versions={1: package_v1, 2: package_v2},
    )

    test = package.Test()
    print(type(package.Test).__name__)
    print(package.Test.__module__)
    print(type(test).__name__)
    print(test.display())
    print(test.log())
    print(test.just_for_test())
    print(test.super_log("Hello", "Alice"))
    print(test.just_for_test())


if __name__ == "__main__":
    main()
