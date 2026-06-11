# LatyChain — 链式数据与规则匹配

> 一个 Python 包，用简洁的 `.xxx.yyy` 语法表达链状结构，
> 并支持用规则链对数据链进行匹配验证。

---

## 快速上手

```python
import LatyChain.ChainDotRule  # 开启 .xxx.yyy 语法
from latychain import Chain

# ── 数据链 ──
heading = .heading.h1
# → Chain(['heading', 'h1'])

path = .user.profile.avatar
# → Chain(['user', 'profile', 'avatar'])

# ── 规则链（含嵌套规则）──
rule = .any(0).enum(
    .admin.any(0),
    .user.any(0)
).rex(r'\d+')
# → Chain([ChainRuleAtom.any(0),
#          ChainRuleAtom.enum(
#            Chain(['admin', ChainRuleAtom.any(0)]),
#            Chain(['user', ChainRuleAtom.any(0)])
#          ),
#          ChainRuleAtom.rex(r'\d+')])

# ── 匹配 ──
.user.login.123.match(rule)    # True
.admin.delete.456.match(rule)  # True
.guest.abc.match(rule)         # False
```

---

## 一、核心概念

### Chain（链）

`Chain` 是 **不可变的有序容器**，元素可以是：
- **字符串** — 表示具体的数据值
- **ChainRuleAtom** — 表示匹配规则

```python
# 纯数据链：全字符串
Chain(['heading', 'h1'])

# 规则链：混有 ChainRuleAtom
Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])

# 混合链
Chain(['a', ChainRuleAtom.any(1), 'b'])
```

### ChainRuleAtom（规则原子）

规则的最小单元，通过 `ChainRuleAtom` 的静态方法创建：

| 方法 | 作用 |
|------|------|
| `ChainRuleAtom.any(min, max)` | 匹配任意个元素（非贪婪带回溯） |
| `ChainRuleAtom.rex(pattern)` | 正则匹配单个元素 |
| `ChainRuleAtom.enum(*chains)` | 枚举选择，匹配其中之一 |
| `ChainRuleAtom.apply(func, long)` | 函数匹配 |
| `ChainRuleAtom.long(min, max)` | 限制单个元素的字符串长度 |
| `ChainRuleAtom.un(value)` | 否定：不等于某值 |
| `ChainRuleAtom.ext(chain?)` | 扩展标记 |

---

## 二、构造 Chain

### 2.1 直接构造

```python
from latychain import Chain

Chain()                        # 空链
Chain(['a'])                   # 单元素
Chain(['a', 'b', 'c'])         # 多元素
Chain([ChainRuleAtom.any(0)])  # 含规则
```

### 2.2 语法糖 `.xxx.yyy`（推荐）

```python
import LatyChain.ChainDotRule

.a.b.c            # → Chain(['a', 'b', 'c'])
.any(0).uuu       # → Chain([ChainRuleAtom.any(0), 'uuu'])
```

import hook 在编译期将 `.xxx` 语法变换为 `Chain([...])` 构造。

**解析规则**：

```
.xxx              → 字符串 'xxx'
.xxx()            → ChainRuleAtom.xxx()
.xxx().yyy.zzz()  → Chain([ChainRuleAtom.xxx(), 'yyy', ChainRuleAtom.zzz()])
```

**不受影响的情况**：

```python
obj.attr          # 对象属性，不动
.5 + .3           # 浮点数，不动
func().attr       # 方法返回值，不动
".heading.h1"     # 字符串字面量，不动
```

---

## 三、使用 Chain

### 3.1 只读访问

```python
c = Chain(['a', 'b', 'c'])

len(c)       # 3
c[0]         # 'a'
c[-1]        # 'c'
list(c)      # ['a', 'b', 'c']
c.elements   # ('a', 'b', 'c')
```

### 3.2 字符串表示

```python
str(Chain(['a', 'b']))   # ".a.b"
str(Chain())             # "."
```

### 3.3 比较与哈希

```python
Chain(['a', 'b']) == Chain(['a', 'b'])   # True

d = {Chain(['a']): 1}  # 可哈希，可作字典键
```

### 3.4 连接

```python
Chain(['a', 'b']) + Chain(['c', 'd'])
# → Chain(['a', 'b', 'c', 'd'])
```

---

## 四、匹配

### 4.1 基本匹配

```python
data = Chain(['x', 'uuu', 'x1'])
rule = Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])

data.match(rule)   # True

# 等价于语法糖
import LatyChain.ChainDotRule
.x.uuu.x1.match(.any(0).uuu.rex(r'x\d'))  # True
```

### 4.2 匹配语义

从左到右顺序匹配，`any` 使用 **非贪婪回溯**。

| data 元素 | pattern 元素 | 匹配方式 |
|-----------|-------------|---------|
| `'a'` | `'a'` | 精确相等 |
| `'a'` | `'b'` | 不匹配 |
| `'a'` | `ChainRuleAtom.any(...)` | 非贪婪尝试各种长度 |
| `'a'` | `ChainRuleAtom.rex(r'\d')` | 正则 fullmatch |
| `'a'` | `ChainRuleAtom.un('a')` | 不等于 'a' 则匹配 |
| `'a'` | `ChainRuleAtom.long(2, 4)` | 字符串长度 2~4 则匹配 |

### 4.3 完整 vs 前缀匹配

```python
data.match(rule)                # 完全匹配（默认）
data.match(rule, partial=True)  # 前缀匹配
```

### 4.4 规则详解

#### `any(min=0, max=0)` — 无限制匹配

```
.aaa.bbb 匹配 .any(0).bbb    → True   (any 吃 0 个)
.aaa.bbb 匹配 .any(1).bbb    → True   (any 吃 1 个)
.aaa.bbb 匹配 .any(2)        → True   (any 吃 2 个)
.aaa.bbb 匹配 .any(3).bbb    → False  (any 吃光，bbb 没东西)
```

参数：`min`（最小匹配数），`max`（最大匹配数，0=无上限）。

#### `rex(pattern)` — 正则匹配

```python
.rex(r'h[12]')  匹配 .h1 .h2
.rex(r'\d+')    匹配 .123
```

对单个链节做 `fullmatch`。

#### `enum(*chains)` — 枚举选择

```python
.enum(
    .type.h1,
    .type.h2
)
# 匹配 .type.h1 或 .type.h2
```

每个参数是一个 Chain（规则或数据均可），匹配其中之一即成功。

#### `apply(func, long=1)` — 自定义匹配

```python
.apply(lambda seg: str(seg).startswith('.x'))
# 单独链节以 'x' 开头

.apply(lambda seg: len(seg) > 2, long=2)
# 连续 2 个链节传入函数
```

`func` 接收一个 `Chain` 对象，返回 `bool`。`long` 指定取几个链节。

常用于在规则链中插入自定义逻辑，或扩展已有规则的行为。

#### `long(min, max=None)` — 长度约束

```python
.long(3)       # 链节长度恰好 3
.long(3, 5)    # 链节长度 3~5
```

只对单个链节生效。

#### `un(value)` — 否定

```python
.un('admin')
# 匹配任何不是 'admin' 的链节
```

#### `ext(chain=None)` — 可选段

标记当前位置可选——匹配时尝试匹配 ext 内部的 chain，匹配不上就跳过。

```python
.a.ext(.pi).b
# 可匹配 .a.pi.b  (ext 匹配了 .pi)
# 也可匹配 .a.b    (ext 跳过了)

.a.b.c.ext(.d.e)
# 可匹配 .a.b.c.d.e
# 也可匹配 .a.b.c
```

---

## 五、完整示例

### 5.1 HTML 标题层级

```python
import LatyChain.ChainDotRule
from latychain import Chain

# 数据
h1 = .heading.h1
h2 = .heading.h2

# 规则：任意前缀 + .heading 后跟 h1~h6
heading_rule = .any(0).heading.rex(r'h[1-6]')

h1.match(heading_rule)    # True
.h2.match(heading_rule)   # True (直接用 . 语法)
.body.h2.match(heading_rule)  # True
```

### 5.2 路径权限检查

```python
import LatyChain.ChainDotRule

# 规则：允许 /user/* /admin/* 但拒绝 /admin/secret
allow_rule = .any(0).enum(
    .user,
    .admin.un('secret')
)

.path.a.user.match(allow_rule)        # True
.path.a.admin.dashboard.match(allow_rule)  # True
.path.a.admin.secret.match(allow_rule)      # False
```

### 5.3 日志分类

```python
import LatyChain.ChainDotRule

# 匹配错误日志：.YYYY.MM.DD.ERROR.xxx
error_pattern = .rex(r'\d{4}').rex(r'\d{2}').rex(r'\d{2}').ERROR.any(0)

.2024.01.15.ERROR.timeout.match(error_pattern)   # True
.2024.01.15.INFO.request.match(error_pattern)     # False
```

### 5.4 配置节解析

```python
import LatyChain.ChainDotRule

# 匹配 [database] -> [connection] -> [pool] ...
config_rule = .database.connection.pool.apply(
    lambda seg: int(str(seg).split('.')[-1]) > 0
)

.database.connection.pool.5.match(config_rule)   # True
.database.connection.pool.0.match(config_rule)   # False
.database.connection.timeout.match(config_rule)  # False
```

---

## 六、API 参考

### `Chain` 类

```python
class Chain:
    def __init__(self, elements=()):
        """elements: 字符串 和/或 ChainRuleAtom 的列表"""

    # ── 只读 ──
    def __getitem__(self, index) -> str | ChainRuleAtom: ...
    def __len__(self) -> int: ...
    def __iter__(self): ...
    @property
    def elements(self) -> tuple: ...

    # ── 字符串 ──
    def __str__(self) -> str: ...    # ".a.b.c"
    def __repr__(self) -> str: ...   # "Chain(['a', 'b', 'c'])"

    # ── 值语义 ──
    def __eq__(self, other) -> bool: ...
    def __hash__(self) -> int: ...

    # ── 运算 ──
    def __add__(self, other) -> Chain: ...
    def match(self, pattern: Chain, partial=False) -> bool: ...

    # ── 工具 ──
    def to_list(self) -> list: ...
    def startswith(self, prefix) -> bool: ...
```

### `ChainRuleAtom` 工厂

```python
class ChainRuleAtom:
    @staticmethod
    def any(min: int = 0, max: int = 0) -> ChainRuleAtom: ...
    @staticmethod
    def rex(pattern: str) -> ChainRuleAtom: ...
    @staticmethod
    def enum(*alternatives: Chain) -> ChainRuleAtom: ...
    @staticmethod
    def apply(func: callable, long: int = 1) -> ChainRuleAtom: ...
    @staticmethod
    def long(min: int, max: int | None = None) -> ChainRuleAtom: ...
    @staticmethod
    def un(value: str) -> ChainRuleAtom: ...
    @staticmethod
    def ext(pattern: Chain | None = None) -> ChainRuleAtom: ...
```

### `LatyChain.ChainDotRule` — import hook

```python
import LatyChain.ChainDotRule
# 自动注册，全局生效。此后 .xxx.yyy 语法可用。
```

---

## 七、设计理念

### 为什么用 import hook？

`.xxx.yyy` 这种语法在 Python 中不是合法的表达式。import hook 在编译期识别 `.xxx` 模式并变换为 `Chain([...])` 构造，让用户以最少的符号写出链状结构。

属性语法（`Chain.xxx.yyy`）不可行，因为它无法区分 `.unlim` 是追加字符串 `'unlim'` 还是调用方法 `unlim()`——解释器在 `__getattr__` 阶段看不到后面有没有 `()`。

### 为什么只有一种类型？

数据链和规则链共用 `Chain` 容器，元素可以是字符串或 `ChainRuleAtom`。不需要两套 API，心智负担低。

### 为什么 Chain 不可变？

- 可哈希，可作字典键
- 线程安全
- 无副作用传递

---

## 八、常见问题

### Q: `ext()` 和 `any()` 的区别？

`any()` 匹配**任意个元素**（带回溯）。`ext()` 表示**可选段**——要么完整匹配内部 chain，要么跳过。

```python
.any(0).b      # .a.b  / .x.y.b  / .b  均可
.ext(.a).b     # .a.b 或 .b ，不能 .x.y.b
```

### Q: 没有 import hook 可以用吗？

可以，用 `Chain([...])` 显式构造：

```python
from latychain import Chain

data = Chain(['heading', 'h1'])
rule = Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])
data.match(rule)
```

### Q: `ext()` 和 `apply()` 的定位？

`ext()` 是**可选段**——匹配时尝试匹配内部 chain，失败则跳过。`apply()` 是**自定义匹配**——用户传入函数，自由定义匹配逻辑。两者不冲突，可以在同一个规则链中使用。

```python
.a.ext(.b).apply(my_check).c
# 匹配 .a.b.<满足my_check>.c
# 或  .a.<满足my_check>.c
```
