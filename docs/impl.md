# LatyChain 实现设计

---

## 一、包结构

```
LatyChain/
  ChainDotRule.py        # 入口：import 即注册 hook
latychain/
  __init__.py             # 导出 Chain, ChainRuleAtom
  _chain.py               # Chain 类
  _atoms.py               # ChainRuleAtom + 各原子子类
  _hook.py                # tokenize 扫描 + 解析器 + import hook 注册
```

### 依赖关系

```
ChainDotRule → _hook (注册)
_hook        → 无编译期依赖（变换产生字符串，运行时才引用 _chain, _atoms）
_chain       → _atoms (match 方法引用原子类)
_atoms       → _chain (Enum, Ext 等接收 Chain 参数)
```

---

## 二、Chain 类 (`_chain.py`)

```python
class Chain:
    """不可变的有序容器。元素可以是 str 或 ChainRuleAtom。"""

    _data: tuple[str | ChainRuleAtom, ...]

    def __init__(self, elements=()):
        self._data = tuple(elements)

    # ── 只读 ──
    def __getitem__(self, index):    return self._data[index]
    def __len__(self) -> int:        return len(self._data)
    def __iter__(self):              return iter(self._data)
    @property
    def elements(self):              return self._data

    # ── 字符串 ──
    def __str__(self) -> str:
        if not self._data:
            return "."
        return "." + ".".join(
            str(e) if not isinstance(e, str) else e
            for e in self._data
        )

    def __repr__(self) -> str:
        return f"Chain({list(self._data)!r})"

    # ── 值语义 ──
    def __eq__(self, other):
        if isinstance(other, Chain):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._data)

    # ── 运算 ──
    def __add__(self, other) -> Chain:
        if isinstance(other, Chain):
            return Chain([*self._data, *other._data])
        return NotImplemented

    def match(self, pattern: Chain, partial: bool = False) -> bool:
        consumed = _backtrack_match(self._data, 0, pattern._data, 0)
        if consumed is None:
            return False
        return True if partial else consumed == len(self._data)

    # ── 工具 ──
    def to_list(self):               return list(self._data)
    def startswith(self, prefix):    return prefix.match(self, partial=True)
```

---

## 三、ChainRuleAtom 类 (`_atoms.py`)

### 基类

```python
class ChainRuleAtom:
    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        """返回所有可能的消耗长度（从小到大）。空列表 = 不匹配。"""
        raise NotImplementedError

    def __str__(self):     ...
    def __repr__(self):    ...
    def __eq__(self, other): ...
    def __hash__(self):    ...
```

### 子类

| 子类 | 构造参数 | 语义 | match_lengths |
|------|---------|------|---------------|
| `_Any` | min, max | 匹配 min~max 个元素 | `range(min, min(upper, remaining))` |
| `_Rex` | pattern | 正则 fullmatch 单元素 | `[1]` 或 `[]` |
| `_Enum` | alternatives: Chain列表 | 择一匹配 | `[consumed]` 或 `[]` |
| `_Apply` | func, long | 函数匹配 long 个元素 | `[long]` 或 `[]` |
| `_Long` | min_len, max_len | 单元素长度约束 | `[1]` 或 `[]` |
| `_Un` | value | 否定：不等于 value | `[1]` 或 `[]` |
| `_Ext` | chain | 可选段：匹配或跳过 | `[0]` 或 `[0, consumed]` |

### 工厂方法

```python
class ChainRuleAtom:
    @staticmethod
    def any(min=0, max=0):        return _Any(min, max)
    @staticmethod
    def rex(pattern):             return _Rex(pattern)
    @staticmethod
    def enum(*alternatives):      return _Enum(list(alternatives))
    @staticmethod
    def apply(func, long=1):      return _Apply(func, long)
    @staticmethod
    def long(min, max=None):      return _Long(min, max)
    @staticmethod
    def un(value):                return _Un(value)
    @staticmethod
    def ext(chain=None):          return _Ext(chain)
```

---

## 四、匹配引擎

```python
def _backtrack_match(data, data_pos, pattern, pat_pos):
    """带回溯的顺序匹配。返回 data 侧消耗的元素数，失败返回 None。"""

    if pat_pos >= len(pattern):
        return 0  # 规则匹配完

    elem = pattern[pat_pos]

    if isinstance(elem, str):
        if data_pos < len(data) and data[data_pos] == elem:
            rest = _backtrack_match(data, data_pos + 1, pattern, pat_pos + 1)
            return (1 + rest) if rest is not None else None
        return None

    if isinstance(elem, ChainRuleAtom):
        for length in elem.match_lengths(data, data_pos):
            rest = _backtrack_match(data, data_pos + length, pattern, pat_pos + 1)
            if rest is not None:
                return length + rest
        return None

    raise TypeError(f"pattern 中有非法元素: {type(elem).__name__}")
```

**要点**：
- `match_lengths` 返回从小到大 → 非贪婪
- 深度优先回溯，找到第一个可行路径即返回
- `_Ext` 返回 `[0, consumed]` → 优先尝试跳过

---

## 五、Import Hook (`_hook.py`)

### 整体策略

**不使用正则，不使用 AST。** 用 Python 标准库 `tokenize` 做词法分析，它在遍历 token 时**自动跳过字符串和注释**，我们只需关注 `OP '.' + NAME` 模式的 token 序列。

```
tokenize 遍历源码 token 流
  │
  ├── STRING token     → 跳过（字符串内部不变换）
  ├── COMMENT token    → 跳过（注释内部不变换）
  ├── OP '.' + NAME    → 可能是一个 .xxx 表达式
  │     │
  │     └── read_dot_expr() 从源码该位置读出完整表达式
  │           │
  │           └── parse_dot_expr() 递归解析为 Python 代码
  │
  └── 其他 token       → 保持原样
```

### 5.1 `transform_source()` — tokenize 遍历 + 源码替换

```python
import tokenize
import io


def transform_source(source: str) -> str:
    """将源码中所有 .xxx.yyy.zzz() 表达式变换为 Chain([...])。"""
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))

    # 收集所有替换 (开始偏移, 结束偏移, 替换文本)
    replaces = []

    for i, tok in enumerate(tokens):
        # 跳过字符串和注释内部
        if tok.type in (tokenize.STRING, tokenize.COMMENT):
            continue

        # 找到 OP '.' + NAME 模式
        if (tok.type == tokenize.OP
            and tok.string == '.'
            and i + 1 < len(tokens)
            and tokens[i + 1].type == tokenize.NAME
            and tokens[i + 1].string[0].isalpha()):

            # 计算源码中的字节偏移
            byte_offset = _token_start_to_offset(source, tok)
            expr, end_offset = read_dot_expr(source, byte_offset)
            transformed = parse_dot_expr(expr)
            replaces.append((byte_offset, byte_offset + len(expr), transformed))

    # 从右到左替换，避免偏移变化
    replaces.sort(key=lambda x: x[0], reverse=True)
    result = list(source)
    for start, end, text in replaces:
        result[start:end] = text
    return ''.join(result)


def _token_start_to_offset(source: str, tok) -> int:
    """将 token 的 (行号, 列号) 转换为源码字符串中的偏移。"""
    lines = source.split('\n')
    return sum(len(l) + 1 for l in lines[:tok.start[0] - 1]) + tok.start[1]
```

### 5.2 `read_dot_expr()` — 从源码读取完整表达式

```python
def read_dot_expr(source: str, pos: int) -> tuple[str, int]:
    """从源码 pos 位置读取完整的 .xxx.yyy.zzz()。
    返回 (表达式字符串, 结束偏移)。
    """
    start = pos
    assert source[pos] == '.'
    pos += 1

    # 读名字
    while pos < len(source) and (source[pos].isalnum() or source[pos] == '_'):
        pos += 1

    # 读 (args) — 栈式括号匹配，支持嵌套
    if pos < len(source) and source[pos] == '(':
        depth = 1
        pos += 1
        while pos < len(source) and depth > 0:
            if source[pos] == '(':
                depth += 1
            elif source[pos] == ')':
                depth -= 1
            pos += 1

    # 继续读后续 .xxx / .xxx() 段
    while pos < len(source) and source[pos] == '.':
        if pos + 1 < len(source) and source[pos + 1].isalpha():
            pos += 1
            while pos < len(source) and (source[pos].isalnum() or source[pos] == '_'):
                pos += 1
            if pos < len(source) and source[pos] == '(':
                depth = 1
                pos += 1
                while pos < len(source) and depth > 0:
                    if source[pos] == '(':
                        depth += 1
                    elif source[pos] == ')':
                        depth -= 1
                    pos += 1
        else:
            break

    return source[start:pos], pos
```

### 5.3 `parse_dot_expr()` — 解析表达式为 Python 代码

```python
def parse_dot_expr(expr: str) -> str:
    """.any(0).uuu.rex(r'x\\d') → Chain([ChainRuleAtom.any(0), 'uuu', ...])"""
    segments = []
    pos = 0

    while pos < len(expr):
        assert expr[pos] == '.'
        pos += 1

        start = pos
        while pos < len(expr) and (expr[pos].isalnum() or expr[pos] == '_'):
            pos += 1
        name = expr[start:pos]

        if pos < len(expr) and expr[pos] == '(':
            args_start = pos + 1
            depth = 1
            pos += 1
            while pos < len(expr) and depth > 0:
                if expr[pos] == '(':
                    depth += 1
                elif expr[pos] == ')':
                    depth -= 1
                pos += 1
            args = expr[args_start:pos - 1]
            segments.append(f"ChainRuleAtom.{name}({_transform_args(args)})")
        else:
            segments.append(repr(name))

    return f"Chain([{', '.join(segments)}])"


def _transform_args(args: str) -> str:
    """递归变换参数中的 .xxx 表达式。"""
    parts = []
    for arg in _split_args(args):
        arg = arg.strip()
        if arg.startswith('.'):
            parts.append(parse_dot_expr(arg))
        else:
            parts.append(arg)
    return ', '.join(parts)


def _split_args(args: str) -> list[str]:
    """按逗号分割，括号内的逗号不分割。"""
    depth = 0
    current = []
    result = []
    for c in args:
        if c in '([':
            depth += 1
            current.append(c)
        elif c in ')]':
            depth -= 1
            current.append(c)
        elif c == ',' and depth == 0:
            result.append(''.join(current).strip())
            current = []
        else:
            current.append(c)
    if current:
        result.append(''.join(current).strip())
    return [r for r in result if r]
```

### 5.4 变换对照表

| 源码 | 变换结果 |
|------|----------|
| `.heading.h1` | `Chain(['heading', 'h1'])` |
| `.a.b.c` | `Chain(['a', 'b', 'c'])` |
| `.any(0).uuu` | `Chain([ChainRuleAtom.any(0), 'uuu'])` |
| `.any(0).uuu.rex(r'x\\d')` | `Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\\d')])` |
| `.any(0).uuu.enum(.hi.rex(r'x[0-9]'), .wuhu.apply(f))` | `Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.enum(Chain(['hi', ChainRuleAtom.rex(r'x[0-9]')]), Chain(['wuhu', ChainRuleAtom.apply(f)]))])` |
| `.a.ext(.b).c` | `Chain(['a', ChainRuleAtom.ext(Chain(['b'])), 'c'])` |

### 5.5 Import Hook 注册

```python
import sys
import os
import importlib.abc
import importlib.util


class _LatyLoader(importlib.abc.Loader):
    def __init__(self, origin: str):
        self.origin = origin

    def exec_module(self, module):
        with open(self.origin, 'r', encoding='utf-8') as f:
            source = f.read()
        transformed = transform_source(source)
        code = compile(transformed, self.origin, 'exec')
        module.__file__ = self.origin
        module.__loader__ = self
        exec(code, module.__dict__)


class _LatyFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        for entry in (path or sys.path):
            if not entry:
                continue
            filename = os.path.join(entry, f"{fullname.replace('.', '/')}.py")
            if os.path.exists(filename):
                return importlib.util.spec_from_loader(
                    fullname, _LatyLoader(filename),
                    origin=filename, is_package=False
                )
        return None


_registered = False


def register():
    global _registered
    if not _registered:
        sys.meta_path.insert(0, _LatyFinder())
        _registered = True
```

---

## 六、各模块 `__init__`

### `latychain/__init__.py`

```python
from latychain._chain import Chain
from latychain._atoms import ChainRuleAtom

__all__ = ["Chain", "ChainRuleAtom"]
```

### `LatyChain/ChainDotRule.py`

```python
"""导入此模块即注册 .xxx.yyy 语法糖。"""
import latychain._hook
latychain._hook.register()
```

### `LatyChain/__init__.py`

```python
# 空
```

---

## 七、边界情况

| 场景 | tokenize 能否正确处理 |
|------|----------------------|
| `"hello .foo.bar"` 字符串中 | ✅ tokenize 标为 STRING，跳过 |
| `# .foo.bar` 注释中 | ✅ tokenize 标为 COMMENT，跳过 |
| `f"{.x}"` f-string 中 | ✅ tokenize 标为 STRING，跳过 |
| `''' .foo '''` 三引号中 | ✅ tokenize 正确处理三引号 |
| `'\\'.foo'` 转义引号 | ✅ tokenize 正确处理转义 |
| `.5 + .3` 浮点数 | ✅ `tokenize.OP '.'` 后的 token 是 NUMBER 不是 NAME |
| `obj.attr` 属性访问 | ✅ `.` 前的 token 是 NAME 不是 OP，但 tokenize 本身不区分——我们在 `tok.type == OP` 时只匹配 `.` 本身，但 `obj.attr` 中 `.` 也是 OP。需要额外检查：`.` 前一个 token 不能是 NAME/OP/NUMBER？ |
| `func().attr` | 同上 |

关于 `obj.attr` 的处理：`tokenize` 会把 `obj.attr` 切为 `[NAME('obj'), OP('.'), NAME('attr')]`，`obj .attr` 也是 `[NAME, OP, NAME]`。两者在 token 序列上无法区分。

**解决方案**：在 `read_dot_expr()` 中，表达式读取后检查：如果读取的表达式前面紧跟着一个 NAME/OP/NUMBER token（即 `obj.attr` 场景），则跳过这次替换。实现方式——检查 `.` 之前的 token：

```python
# 在 transform_source 中找到 OP '.' 时：
if i > 0 and tokens[i-1].type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER):
    continue  # 前面有表达式，可能是 obj.attr，跳过
```

这个检查在 tokenize 层面就完成，比字符级前置排除更可靠。

---

## 八、实现顺序

| 步 | 内容 | 依赖 |
|----|------|------|
| 1 | `_atoms.py` — ChainRuleAtom 基类 + 7 子类 | 无 |
| 2 | `_chain.py` — Chain + `_backtrack_match` | _atoms |
| 3 | 单元测试：Chain 操作 + 各原子匹配 | _chain, _atoms |
| 4 | 单元测试：回溯匹配 | _chain, _atoms |
| 5 | `_hook.py` — tokenize 变换 + import hook | 无编译期依赖 |
| 6 | `LatyChain/ChainDotRule.py` | _hook |
| 7 | `__init__.py` | 全部 |
| 8 | 集成测试 | 全部 |
