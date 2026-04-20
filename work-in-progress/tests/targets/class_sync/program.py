"""class sync の実行対象プログラム。

期待する出力:
3.00,4.00
5.00
5.00,0.93
0.00,0.00
"""

from __future__ import annotations

from . import package_sync, package_v1, package_v2
from ..support import compile_and_load_package


def main() -> None:
    package = compile_and_load_package(
        __file__,
        versions={1: package_v1, 2: package_v2},
        class_syncs={
            "Point": {
                (1, 2): package_sync.sync_point_from_v1_to_v2,
                (2, 1): package_sync.sync_point_from_v2_to_v1,
            }
        },
        class_attributes={
            "Point": {
                1: ("x", "y"),
                2: ("r", "theta"),
            }
        },
    )

    point = package.Point(3.0, 4.0)

    x, y = point.get_cartesian()
    print(f"{x:.2f},{y:.2f}")

    print(f"{point.r:.2f}")

    r, theta = point.get_polar()
    print(f"{r:.2f},{theta:.2f}")

    point.r = 0.0
    x, y = point.get_cartesian()
    print(f"{x:.2f},{y:.2f}")


if __name__ == "__main__":
    main()
