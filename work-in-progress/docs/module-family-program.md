# モジュールファミリ生成プログラム

これは、通常の Python import で読み込まれた複数版 module から、
1 つの logical module program を生成するための最小実装である。

この段階では Python の import machinery は変更しない。

## 公開 API

利用側は、まず version ごとの module を通常通り import する。

```python
import package_v1
import package_v2
import mv

package = mv.compile_module_family(
    versions={1: package_v1, 2: package_v2},
)

mv.install_logical_module(package)
```

module 名から import も含めて行う場合は `load_module_family(...)` を使う。

```python
import mv

mv.load_module_family(
    versions={1: "package_v1", 2: "package_v2"},
)
```

logical module program を `.py` として書き出してから load する場合は、
`compile_module_family_program(...)` と `load_module_program(...)` を使う。

```python
generated_path = mv.compile_module_family_program(
    versions={1: package_v1, 2: package_v2},
    output_path="generated/package.py",
)

package = mv.load_module_program(generated_path, "package")
```

その後、下流コードは logical module を import して使う。

```python
import package

package.field(1)
package.method(1, "left", "right")
package.Box("item")
```

top-level function は、version と通常引数を受け取る generated wrapper function
として配置する。値や通常 object は、version を受けて対応する実体を返す
generated selector として配置する。

top-level value/object は generated selector function として配置する。
専用 class は使わない。version 指定を省略した場合は、直前に使った version を継続する。

```python
package.field()    # 初期 version の値
package.field(2)   # version 2 の値を取得し、現在 version を 2 にする
package.field()    # version 2 を継続する
```

class member は generated class として配置する。`package.Box(...)` は通常の
class 呼び出しとして instance を作る。
version ごとの method set class を確認したい場合は `package.Box.implementation(1)` を使う。

現在の主 API は次の 2 つである。

- `compile_module_family(...)`
  - すでに import 済みの module object から logical module を作る
- `load_module_family(...)`
  - module 名を import してから logical module を作る

`compose_module_family(...)` は互換用 alias として残している。

## compile 時に行うこと

`compile_module_family(...)` は、同じ生成 source を module namespace で実行して
plain module object を返す。`compile_module_family_program(...)` はその生成
source を `.py` として書き出す。どちらも同じ生成経路を使う。

compile 時には以下を行う。

- logical module 名を決める
  - 省略時は `package_v1` のような module 名から `_vN` を取り除いて推論する
- logical member と version ごとの実名対応を作る
  - `member_map` がなければ、同名 member を自動対応する
  - `member_map` があれば、指定された対応を使う
- logical member ごとに生成する Python 定義の形を決める
- top-level function/value は module-level wrapper/selector function として生成する
- class は archive 版の生成クラスに近い構造の generated class として生成する

`compile_module_family_program(...)` の場合は、上記と同じ logical member 情報を
Python source として出力する。出力された program は以下のような形になる。

```python
import importlib as _versioned_importlib

versions = (1, 2)
_versioned_modules = {
    1: _versioned_importlib.import_module("package_v1"),
    2: _versioned_importlib.import_module("package_v2"),
}

_field_current_version = 1

def field(version=None):
    global _field_current_version
    if version is None:
        version = _field_current_version
    _field_current_version = version
    if version == 1:
        return _versioned_modules[1].field
    if version == 2:
        return _versioned_modules[2].field
    raise KeyError(...)

def method(version, *args, **kwargs):
    if version == 1:
        return _versioned_modules[1].method(*args, **kwargs)
    if version == 2:
        return _versioned_modules[2].method(*args, **kwargs)
    raise KeyError(...)

class Point:
    __module__ = __name__
    _switch_count = 0
    versions = (1, 2)

    # 版ごとの呼び分けは生成時にクラス定義へ展開する。
    # 実行時に関数形状を調べる処理はここには残さない。

    class _V1_Impl(object):
        _version_number = 1

        def __initialize__(self, x, y, *, _wrapper_self=None):
            if _wrapper_self is not None:
                self = _wrapper_self
            self.x = x
            self.y = y

        def get_cartesian(self, *, _wrapper_self=None):
            if _wrapper_self is not None:
                self = _wrapper_self
            return (self.x, self.y)

    class _V2_Impl(object):
        _version_number = 2

        def __initialize__(self, r, theta, *, _wrapper_self=None):
            if _wrapper_self is not None:
                self = _wrapper_self
            self.r = r
            self.theta = theta

        def get_polar(self, *, _wrapper_self=None):
            if _wrapper_self is not None:
                self = _wrapper_self
            return (self.r, self.theta)

    _POINT_VERSION_INSTANCES_SINGLETON = [_V1_Impl(), _V2_Impl()]

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "_is_switching", False)
        self._point_current_state = self._POINT_VERSION_INSTANCES_SINGLETON[0]
        try:
            return self._point_current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
        except (AttributeError, TypeError):
            if len(args) <= 2 and kwargs.keys() <= {"x", "y"} and ...:
                self._point_switch_to_version(1)
                return self._point_current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
            if len(args) <= 2 and kwargs.keys() <= {"r", "theta"} and ...:
                self._point_switch_to_version(2)
                return self._point_current_state.__initialize__(*args, _wrapper_self=self, **kwargs)
            raise TypeError(...)

    def _point_switch_to_version(self, version_num):
        ...

    @staticmethod
    def sync_point_from_v1_to_v2(wrapper_obj):
        wrapper_obj.r = ...
        wrapper_obj.theta = ...

    @property
    def r(self):
        try:
            return self._r
        except AttributeError:
            self._point_switch_to_version(2)
            return self._r

    @r.setter
    def r(self, value):
        try:
            self._r
        except AttributeError:
            if not object.__getattribute__(self, "_is_switching"):
                self._point_switch_to_version(2)
        self._r = value

    def get_cartesian(self):
        try:
            return self._point_current_state.get_cartesian(_wrapper_self=self)
        except AttributeError:
            self._point_switch_to_version(1)
            return self._point_current_state.get_cartesian(_wrapper_self=self)

    def get_polar(self, *args, **kwargs):
        ...
```

生成された program は `mv` の実装を import しない。
複数版 class 管理に必要な処理は、生成された class 定義内に展開される。

## member_map

version 間で名前が違う場合は `member_map` を渡す。

```python
package = mv.compile_module_family(
    versions={1: package_v1, 2: package_v2},
    member_map={
        "field": {1: "field", 2: "renamed_field"},
        "method": {1: "method", 2: "renamed_method"},
    },
)
```

この場合、対応関係は compile 時の管理情報として使う。
ただし現段階では、名前が異なる member は module 上でも別の公開名として出す。

```python
package.field(1)
package.renamed_field(2)
package.method(1, "x")
package.renamed_method(2, "x")
```

名前が異なる member は、無理に 1 つの公開名へまとめない。
module 上では実名ごとの生成済み object として配置する。

```python
package.method(1, "x")           # version 1 の method を呼ぶ
package.renamed_method(2, "x")   # version 2 の renamed_method を呼ぶ
```

## 生成済み object

module に配置される object は member 種別ごとに異なる。

- function / value / external / object
  - function / external callable は `package.member(version, *args, **kwargs)` で呼ぶ
  - value / object は `package.member(version)` または `package.member()` で実体を返す
- class
  - `package.ClassName` 自体が generated class
  - `package.ClassName(...)` はその class の instance を返す
  - version ごとの method 本体は generated class 内の `_Vn_Impl` に移される
  - instance は `_point_current_state` のような archive 互換名で active version の method set instance を保持する

generated class が現在持つ機能は以下。

- constructor 引数に合う version を選び、instance 上に状態を作る
- method 呼び出し時に現在 version を優先する
- 現在 version に method がない、または引数が合わない場合は対応 version へ切り替える
- `class_syncs` に登録された sync 関数を version 切り替え時に呼ぶ
- `class_attributes` に登録された属性は、未初期化アクセス時に対応 version へ切り替える

generated class 自体は通常の `class Point:` 定義として出力する。
versioned class の method body は compile 時に取り出し、
`Point._V1_Impl`, `Point._V2_Impl` のような内側 class へ移す。
method set instance は `_POINT_VERSION_INSTANCES_SINGLETON` のような archive 互換名の
singleton list に保持する。
各 method には `_wrapper_self` を追加し、実行時には wrapper instance を
`self` として再束縛する。
constructor / method の分岐は、compile 時に引数条件を解析して
`try` / `except` と静的な `if` 条件として class 定義内へ展開する。
method stub は archive 実装に合わせ、全 version でシグネチャが一致する場合は
具体的な `def display(self):` のような stub を生成し、シグネチャが不一致の場合だけ
`def method(self, *args, **kwargs):` を生成する。
生成された program の実行時には `inspect.signature` や `inspect.getattr_static` は使わない。

## 処理経路

例:

```python
package.method(1, "left", "right")
```

処理は以下。

```text
package.method
  -> logical member "method" の generated wrapper function

generated wrapper function (1, "left", "right")
  -> version 1 に対応する module 内の "method" を取得
  -> 取得した function をそのまま呼ぶ
  -> 戻り値を返す
```

`package.field(1)` の場合は generated selector が version 1 の値を返す。

## テストでの生成物

pytest では各 target program が自分のフォルダ配下に logical module program を書き出す。

```text
work-in-progress/tests/targets/<target>/generated/package.py
```

テストはこの生成ファイルを load して実行する。
pytest 開始時に既存の `generated/` は削除するが、テスト終了時には削除しない。
そのため、失敗時や実装確認時に生成後の logical module program をそのまま読める。

class の場合:

```python
point = package.Point(3.0, 4.0)
point.get_polar()
```

処理は以下。

```text
package.Point
  -> generated class Point

Point(3.0, 4.0)
  -> constructor 引数に合う version を選ぶ
  -> Point instance を作る
  -> active version の method set を _point_current_state にする
  -> 選ばれた version の __initialize__ を Point instance に対して実行する

point.get_polar()
  -> generated class の method stub が呼ばれる
  -> 生成済み try/except と静的 if 条件で version を選ぶ
  -> 必要なら sync 関数を呼んで version を切り替える
  -> _point_current_state の method を Point instance に対して実行する
```

sync を使う場合:

```python
package = mv.compile_module_family(
    versions={1: package_v1, 2: package_v2},
    class_syncs={
        "Point": {
            (1, 2): sync_point_from_v1_to_v2,
            (2, 1): sync_point_from_v2_to_v1,
        }
    },
    class_attributes={
        "Point": {
            1: ("x", "y"),
            2: ("r", "theta"),
        }
    },
)
```

`class_syncs` の sync 関数は generated class の instance を 1 引数で受け取り、状態を更新する。

```python
def sync_point_from_v1_to_v2(wrapper_obj):
    wrapper_obj.r = ...
    wrapper_obj.theta = ...
```

## archive した PoC との関係

archive した旧コンパイラ実装は、クラス単位の AST 変換コンパイラである。
wrapper 生成、`try` / `except` による fast path / slow path、同期処理を考える上で
現在の generated class の参照元にしている。

この生成方式では、class instance の複数版管理を generated class と
その class 定義内に展開された処理に寄せる。
論文の記述に合わせ、method object は version-specific method set として
generated class 内の inner class に置き、instance attribute は wrapper instance 側の
状態として扱う。

現時点で制限が残るもの:

- 複雑な MRO を持つ多重継承
- `super(type, obj)` の高度な書き換え
- classmethod / staticmethod 以外の複雑な descriptor
