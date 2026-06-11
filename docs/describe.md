# latychain 设计文档

`latychain` 是一个包，提供 `Chain` 和 `ChainRule` 两个核心对象。

---

# Chain

**不可变的链式值对象。** 一旦创建不可修改，可哈希，可作字典键。

例如：
- `.heading.h1`
- `.style.font.color.red`
- `.par`

## 定义

三种方式：

### 1. Chain([]) 构造器

```python
a = Chain(['heading', 'h1'])
b = Chain(['style', 'font', 'color', 'red'])
c = Chain(['par'])
```

可构造包含任意字符串的链，包括保留字（如 `'unlim'`、`'regex'`）。

### 2. Chain.xxx 链式语法

```python
a = Chain.heading.h1
b = Chain.style.font.color.red
c = Chain.par
```

每个 `.xxx` 追加一个链节。**所有非保留字名称**都作为链节追加。

### 3. 语法糖（需 import hook）

```python
# 文件第一行: # laty: enable

a = .heading.h1          # → Chain.heading.h1
b = .style.font.color.red
```

详见下文"Import Hook"章节。

## 不可变性

- 无 `append`、`pop`、`remove` 等方法
- 无 `__setitem__`
- 所有"修改"操作（`+` 连接）返回新对象
- 可哈希，可作字典键/集合成员

```python
d = {Chain.a.b: "value"}  # ✅
```

## 运算

### 比较

```python
Chain.a.b == Chain.a.b    # True
Chain.a.b != Chain.a.b.c  # True
```

### in（前缀匹配）

```python
# a in b: a 的前缀是否完全是 b？
#        → "长的链 in 短的链" 为 True

.style.font.color.red in .style.font    # True（长的 in 短的）
.style.font in .style.font.color.red    # False（短的 in 长的）
.font in .style.font.color.red          # False
```

### 运算符

```python
# 连接
.style.font + .color.red == .style.font.color.red    # True

# 索引
chain[0]      # → 'style'
chain[-1]     # → 'red'

# 迭代
list(chain)   # → ['style', 'font', 'color', 'red']
```

### 方法

```python
chain.to_list()          # 转列表
chain.startswith(prefix) # 前缀判断
chain.map(func)          # 映射每个元素返回新链
chain.filter(func)       # 过滤元素返回新链
```

## 术语

| 术语 | 说明 | 例子 |
|------|------|------|
| **链** (chain) | 任意长度的链 | `.style.font.color.red` |
| **链节** (link) | 单段链 | `.style` `.font` |

---

# ChainRule

针对 Chain 的规则，可以作类型约束，也可以直接代码验证。

## 定义

和 Chain 一样用链式语法，但追加了规则函数：

```python
.unlim(0).uuu.enum(
    .hi.regex(r'x[0-9]'),
    .wuhu.apply(lambda seg: str(seg).startswith('.x')).ext(.awo)
)
```

语义：0个或多个任意链节 → `.uuu` → 要么 `.hi` 后跟匹配 `x[0-9]` 的链节，要么 `.wuhu` 后跟满足函数的链节（可扩展 `.awo`）

## 匹配

```python
chain in rule
# 或
rule.match(chain)
```

返回 `True` 或 `False`。

## 规则函数

### unlim(min=1, max=0)

无限制匹配。带回溯引擎，**非贪婪**优先。

| 参数 | 含义 |
|------|------|
| `unlim()` | 至少 1 个任意链节 |
| `unlim(0)` | 0 个或多个任意链节 |
| `unlim(2)` | 至少 2 个 |
| `unlim(1, 3)` | 1~3 个 |
| `unlim(0, 5)` | 0~5 个 |

### regex(pattern: str)

正则匹配**单个链节**（fullmatch）。

```python
.regex(r'x\d')     # 匹配 'x1', 'x9'
.regex(r'h[12]')   # 匹配 'h1', 'h2'
```

### enum(*alternatives)

枚举选择——匹配其中之一。

```python
.enum(
    .type.h1,
    .type.h2
)
```

### apply(func, long=1)

函数匹配。`long` 为取的链节数，`func` 接收一个 Chain 对象。

```python
.apply(lambda seg: len(seg) > 2)        # 单个链节长度>2
.apply(lambda seg: seg[0] == 'x', 2)     # 连续2个链节，第一个是'x'
```

### long(min, max)

**单个链节**的字符串长度约束。

```python
.long(3, 5)   # 链节长度在 3~5 之间
.long(4)      # 链节长度恰好 4
```

### un(value)

否定：不是某个值。

```python
.un('admin')   # 匹配不是 'admin' 的链节
```

### ext(rule=None)

扩展标记。标记当前位置允许追加额外匹配。

---

# 关键设计决策

## 1. 如何区分"追加元素"和"调用方法"？

这是最核心的歧义问题：

```python
Chain.a.b.c          # .a .b .c 都是链节追加
Chain.a.b.unlim()    # .a .b 是链节，.unlim() 是方法调用
```

**解决方案：ChainNode 延迟代理 + 保留字分派**

- `Chain.xxx` 返回 `ChainNode`（不是 `Chain` 本身）
- `ChainNode.__getattr__`：
  - **保留方法名**（`unlim` `regex` `enum` `apply` `long` `ext` `un`）→ 转换为 `ChainRule` 返回对应方法
  - **普通名称** → 追加为链节，返回新 `ChainNode`
  - **常见 Python 方法名**（`append` `pop` `sort` 等）→ 抛出 `AttributeError`，提示 Chain 是不可变常量
- **值上下文**（`str` `repr` `iter` `eq` `hash` 等）→ 自动坍缩为 `Chain`

```
ChainNode(['a','b'])
  ├── .c        → ChainNode(['a','b','c'])
  ├── .unlim()  → ChainRule(['a','b']).unlim()
  └── .append   → ❌ AttributeError（提示链不可变）
```

## 2. Chain 为什么是不可变常量？

- 无副作用的引用传递
- 可哈希，可作字典键
- 线程安全
- 语义清晰：链是"值"而不是"容器"

如果需要"追加"，用 `+` 操作符：
```python
new_chain = old_chain + Chain.c.d   # 返回新链
```

## 3. 回溯匹配引擎

`unlim` 使用**带回溯的非贪婪匹配**：

```
Rule: .unlim(0).uuu.regex(r'x\d')
Chain: .pre.uuu.x1

尝试:
  unlim=0 → .uuu不匹配'pre' → 回溯
  unlim=1 → .uuu不匹配'uuu' → 等等！.uuu匹配了'uuu'
  → regex匹配'x1' ✓
```

回溯按"最短优先"的顺序尝试，保证 `unlim` 尽可能少匹配。

## 4. Import Hook（语法糖）

文件第一行写 `# laty: enable`，导入时自动将 `.xxx.yyy` 变换为 `Chain.xxx.yyy`。

```python
# laty: enable
from latychain import Chain

a = .heading.h1          # → Chain.heading.h1
b = .style.font.color.red
```

不受影响：
- 浮点数：`.5` `.3e10`
- 对象属性：`obj.attr`
- 方法返回：`func().attr`
- 索引访问：`list[0].attr`
- 字符串内部：`".heading.h1"`（注：f-string 中的 `.xxx` 也会被变换）

---

# 补充建议

以下功能可供后续扩展：

### 对 ChainRule

- `not_()` — 否定整个规则
- `optional()` — 可选匹配（0 或 1 次）
- `capture(name)` — 捕获匹配段，类似正则的命名分组
- `where(predicate)` — 对链节值做任意条件判断
- `debug()` — 匹配失败时输出失败位置和期望

### 对 Chain

- `chain.split(delimiter)` — 按某链节分割
- `chain.common_prefix(other)` — 公共前缀
- `chain.replace(old, new)` — 替换元素
- `chain.glob(pattern)` — 类 glob 匹配
