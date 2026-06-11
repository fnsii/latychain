# latychain 设计 v1

**核心理念：只有一个类型 `Chain`，同时承载数据和规则。**

---

## 一、Chain 的定义

`Chain` 是一个不可变的有序容器，元素可以是 **字符串** 或 **ChainRuleAtom（规则原子）**。

```python
# 纯数据链 —— 元素全是字符串
Chain(['heading', 'h1'])

# 规则链 —— 元素混有 ChainRuleAtom
Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x[0-9]')])

# 混合链
Chain(['a', ChainRuleAtom.any(1), 'b', ChainRuleAtom.ext(Chain(['c']))])
```

### 构造方式

只有一种：`Chain(iterable)`。

```python
Chain()                                   # 空链
Chain(['a'])                              # 单元素
Chain(['a', 'b', 'c'])                    # 多元素
Chain([ChainRuleAtom.any(0), 'uuu'])      # 含规则
```

**没有** `Chain.xxx.yyy` 属性语法。  
**没有** `ChainNode` 代理对象。

---

## 二、ChainRuleAtom（规则原子）

`ChainRuleAtom` 是规则的不可变最小单元，通过 `ChainRuleAtom` 的静态方法创建。

| 方法 | 参数 | 含义 |
|------|------|------|
| `ChainRuleAtom.any(min=0, max=0)` | min/max | 无限制匹配（非贪婪带回溯） |
| `ChainRuleAtom.enum(*alternatives)` | Chain 列表 | 选择匹配其中之一 |
| `ChainRuleAtom.rex(pattern)` | str | 正则匹配单个链节 |
| `ChainRuleAtom.apply(func, long=1)` | callable, int | 函数匹配 long 个链节 |
| `ChainRuleAtom.long(min, max?)` | int, int? | 单个链节的字符串长度约束 |
| `ChainRuleAtom.un(value)` | str | 否定：不是某值 |
| `ChainRuleAtom.ext(pattern?)` | Chain? | 扩展标记 |

```python
# 创建规则原子
ChainRuleAtom.any(0)                               # 0个或多个
ChainRuleAtom.rex(r'x\d')                          # 正则
ChainRuleAtom.enum(Chain(['a']), Chain(['b']))     # 选择
ChainRuleAtom.apply(lambda c: len(c) > 2)          # 函数
ChainRuleAtom.long(3, 5)                           # 长度约束
ChainRuleAtom.un('admin')                          # 否定
ChainRuleAtom.ext(Chain(['a', 'b']))               # 扩展
```

这些方法返回的是 `ChainRuleAtom` 实例，可以直接放进 `Chain`。

---

## 三、匹配

### data.match(pattern) → bool

```python
data = Chain(['x', 'uuu', 'hi', 'x1'])
pattern = Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x[0-9]')])

data.match(pattern)   # True
```

### 匹配语义

从左到右顺序匹配，`any` 使用 **非贪婪回溯**。

| data 元素类型 | pattern 元素类型 | 匹配方式 |
| ------------- | ---------------- | -------- |
| 字符串 `'a'`  | 字符串 `'a'`     | 精确相等 |
| 字符串 `'a'`  | 字符串 `'b'`     | 不匹配 |
| 字符串 `'a'`  | ChainRuleAtom | 交给 `ChainRuleAtom.match()` |
| 字符串 `'a'`  | `any(...)` | 非贪婪尝试各种长度 |
| 字符串 `'a'`  | `rex(r'\d')` | fullmatch |
| 字符串 `'a'`  | `un('a')` | 不等于 'a' 则匹配 |

### 完整匹配 vs 前缀匹配

```python
# 完全匹配（默认）
data.match(pattern)       # 必须消耗 data 全部元素

# 前缀匹配（可选）
data.match(pattern, partial=True)  # pattern 匹配 data 的前缀即可
```

---

## 四、Import Hook

### 启用

```python
import LatyChain.ChainDotRule
# 自动注册 import hook，此后导入的模块中 .xxx 语法生效
```

只需在入口处 import 一次，全局生效。被导入的模块不需要额外写任何标记。

### 变换规则

import hook 将 `.xxx` 表达式编译为显式的 `Chain([...])` 构造。

**核心算法**：解析 `.xxx.yyy.zzz()` 链，按是否有 `()` 区分"字符串元素"和"ChainRuleAtom"。

```
语法:  .xxx              →  字符串 'xxx'
       .xxx()            →  ChainRuleAtom.xxx()
       .xxx(args)        →  ChainRuleAtom.xxx(args)
       .xxx().yyy.zzz()  →  混合 Chain([ChainRuleAtom.xxx(), 'yyy', ChainRuleAtom.zzz()])
```

### 变换对照表

| 源码 | 变换结果 |
|------|----------|
| `.heading.h1` | `Chain(['heading', 'h1'])` |
| `.a.b.c` | `Chain(['a', 'b', 'c'])` |
| `.any(0)` | `Chain([ChainRuleAtom.any(0)])` |
| `.any(0).uuu` | `Chain([ChainRuleAtom.any(0), 'uuu'])` |
| `.any(0).uuu.rex(r'x\d')` | `Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])` |
| `.any(0).uuu.enum(.hi.rex(r'x[0-9]'), .wuhu.apply(f))` | `Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.enum(Chain(['hi', ChainRuleAtom.rex(r'x[0-9]')]), Chain(['wuhu', ChainRuleAtom.apply(f)]))])` |
| `.any(0).ext(.awo)` | `Chain([ChainRuleAtom.any(0), ChainRuleAtom.ext(Chain(['awo']))])` |
| `.a.b.ext(.c.d)` | `Chain(['a', 'b', ChainRuleAtom.ext(Chain(['c', 'd']))])` |

### 嵌套规则

`ext(.xxx)` 或 `enum(.a.b, .c.d)` 中的参数也是 `.xxx` 表达式，递归变换。

```python
# 源码 → 变换

.ext(.a.b)
# → Chain([ChainRuleAtom.ext(Chain(['a', 'b']))])


.enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(f)
)
# → Chain([ChainRuleAtom.enum(
#     Chain(['hi', ChainRuleAtom.rex(r'x[0-9]')]),
#     Chain(['wuhu', ChainRuleAtom.apply(f)])
# )])
```

### 不受影响的情况

```python
x = obj.attr          # 对象属性访问，不动
y = .5 + .3           # 浮点数，不动
z = func().attr       # 方法返回值访问，不动
s = ".heading.h1"     # 字符串字面量，不动
```

---

## 五、Import Hook 的解析算法

输入一个 `.xxx.yyy.zzz()` 表达式，输出 `Chain([...])` 构造。

### 步骤

```
1. 去掉开头的 .
2. 按 . 分割为 segments
3. 对每个 segment:
   a. 如果是 name (无括号) → 字符串 'name'
   b. 如果是 name(args) → 规则原子 name(args)
      - args 中如果还有 .xxx 表达式 → 递归解析
4. 包裹为 Chain([...])
```

### 解析伪代码

```
parse_dot_expr(".any(0).uuu.enum(.hi.rex(r'x[0-9]'), .wuhu.apply(f))")
    → segments: ["any(0)", "uuu", "enum(.hi.rex(r'x[0-9]'), .wuhu.apply(f))"]
    → [
        ChainRuleAtom.any(0),                       # 有括号 → ChainRuleAtom
        'uuu',                                      # 无括号 → 字符串
        ChainRuleAtom.enum(                         # 有括号 → ChainRuleAtom，参数递归
          Chain(['hi', ChainRuleAtom.rex(r'x[0-9]')]),
          Chain(['wuhu', ChainRuleAtom.apply(f)])
        )
      ]
    → Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.enum(...)])
```

---

## 六、完整例子

### 纯数据链

```python
import LatyChain.ChainDotRule  # 注册语法
from latychain import Chain

# 纯数据链
heading = .heading.h1
# → Chain(['heading', 'h1'])

style = .style.font.color.red
# → Chain(['style', 'font', 'color', 'red'])

combined = .style.font + .color.red
# → Chain(['style', 'font']) + Chain(['color', 'red'])
# → Chain(['style', 'font', 'color', 'red'])
```

### 规则匹配

```python
import LatyChain.ChainDotRule
from latychain import Chain

# 定义规则
rule = .any(0).uuu.enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(lambda c: str(c).startswith('.x')).ext(.awo)
)

# 匹配
data1 = .x.uuu.hi.x1
data1.match(rule)                     # True

data2 = .x.uuu.wuhu.xhello.awo
data2.match(rule)                     # True

data3 = .uuu.other
data3.match(rule)                     # False
```

---

## 七、API 总览

### Chain 类

```python
class Chain:
    def __init__(self, elements=()): ...

    # 只读
    def __getitem__(self, index): ...
    def __len__(self): ...
    def __iter__(self): ...
    @property
    def elements(self): ...

    # 字符串
    def __str__(self): ...
    def __repr__(self): ...

    # 值语义
    def __eq__(self, other): ...
    def __hash__(self): ...

    # 运算
    def __add__(self, other): ...          # 连接
    def match(self, pattern, partial=False): ...  # 匹配

    # 工具
    def to_list(self): ...
    def startswith(self, prefix): ...
    def map(self, func): ...
    def filter(self, func): ...
```

### ChainRuleAtom 类（规则原子工厂）

```python
class ChainRuleAtom:
    @staticmethod
    def any(min=0, max=0): ...
    @staticmethod
    def enum(*alternatives): ...
    @staticmethod
    def rex(pattern): ...
    @staticmethod
    def apply(func, long=1): ...
    @staticmethod
    def long(min, max=None): ...
    @staticmethod
    def un(value): ...
    @staticmethod
    def ext(pattern=None): ...
```

> 命名说明：`unlim` → `any`（更直观），`regex` → `rex`（更短）。

---

## 八、与旧设计的差异

| 项目 | 旧设计 | 新设计 (v1) |
|------|--------|------------|
| Chain 元素类型 | 仅字符串 | 字符串 + ChainRuleAtom |
| 构造方式 | `Chain([])` + `Chain.xxx.yyy` | 仅 `Chain([])` |
| ChainNode | 有 | 无 |
| 属性语法 `Chain.xxx.yyy` | 有 | 无 |
| 匹配运算符 | `in` | `.match()` |
| ChainRule | 独立类 | 合并为 ChainRuleAtom |
| 命名 | `unlim` / `regex` | `any` / `rex` |
| import hook | 可选语法糖 | 主要使用方式（`import LatyChain.ChainDotRule`） |
