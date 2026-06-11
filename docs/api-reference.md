# API Reference

> **⚠️ Early Development** — API may change.

## Chain

```python
from latychain import Chain
```

### Constructor

```python
Chain(elements=())
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `elements` | `Iterable[str \| ChainRuleAtom]` | `()` | Initial elements |

### Read operations

| Method | Returns | Description |
|--------|---------|-------------|
| `chain[i]` | `str \| ChainRuleAtom` | Indexed access (negative supported) |
| `len(chain)` | `int` | Number of elements |
| `iter(chain)` | `Iterator` | Iterate over elements |
| `chain.elements` | `tuple` | Read-only underlying tuple |

### String representation

| Method | Returns | Example |
|--------|---------|---------|
| `str(chain)` | `str` | `".a.b.c"` |
| `repr(chain)` | `str` | `"Chain(['a', 'b', 'c'])"` |

### Value semantics

| Method | Returns | Description |
|--------|---------|-------------|
| `chain == other` | `bool` | Value equality |
| `hash(chain)` | `int` | Hashable (dict key) |
| `bool(chain)` | `bool` | `True` if non-empty |

### Operations

```python
chain + other             # Concatenation → new Chain
chain.match(pattern)      # Backtracking match (full)
chain.match(pattern, partial=True)  # Prefix match
chain.startswith(prefix)  # Prefix check
chain.to_list()           # → list of elements
```

#### `match(pattern, partial=False)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | `Chain` | — | Pattern chain (strings + ChainRuleAtom) |
| `partial` | `bool` | `False` | If `True`, only match a prefix |

Returns `True` if a match is found.

---

## ChainRuleAtom

```python
from latychain import ChainRuleAtom
```

### `any(min=0, max=0)`

Match between `min` and `max` arbitrary elements. `max=0` means unbounded.

| Example | Meaning |
|---------|---------|
| `ChainRuleAtom.any()` | At least 1 element |
| `ChainRuleAtom.any(0)` | 0 or more |
| `ChainRuleAtom.any(2)` | At least 2 |
| `ChainRuleAtom.any(1, 3)` | 1 to 3 |
| `ChainRuleAtom.any(0, 5)` | 0 to 5 |

Non-greedy with backtracking.

### `rex(pattern)`

Regex `fullmatch` on a **single** string element.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `str` | Regex pattern (compiled with `re.compile`) |

```python
ChainRuleAtom.rex(r'h[12]')     # matches 'h1', 'h2'
ChainRuleAtom.rex(r'\d+')       # matches '123', '0'
ChainRuleAtom.rex(r'x[0-9]')    # matches 'x0'..'x9'
```

### `enum(*alternatives)`

Pick **one** of several alternative chains.

```python
pat = Chain([ChainRuleAtom.enum(
    Chain(['type', 'h1']),
    Chain(['type', 'h2']),
)])
# matches .type.h1 or .type.h2
```

### `apply(func, long=1)`

Match `long` consecutive elements via a user-supplied predicate.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `callable(Chain) -> bool` | — | Predicate receiving a Chain |
| `long` | `int` | `1` | Number of elements to pass to func |

```python
ChainRuleAtom.apply(lambda seg: str(seg).startswith('.x'))
ChainRuleAtom.apply(lambda seg: seg[0] != seg[1], long=2)
```

### `long(min, max=None)`

Constrain the **string length** of a single element.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min` | `int` | — | Minimum length (inclusive) |
| `max` | `int \| None` | `None` | Maximum length; `None` = exact match |

```python
ChainRuleAtom.long(3)         # exactly 3: 'abc' ✓, 'ab' ✗
ChainRuleAtom.long(2, 5)      # 2 to 5 characters
```

### `un(value)`

Match any single element **not equal** to `value`.

```python
ChainRuleAtom.un('admin')     # matches 'user', 'guest'; not 'admin'
```

### `ext(chain=None)`

Optional segment: try matching `chain`, or skip (consume 0).

```python
ChainRuleAtom.ext()             # always skips
ChainRuleAtom.ext(Chain(['a'])) # matches 'a' or skips
```

---

## `latychain.ChainDotRule`

Import hook that enables `.xxx.yyy` syntax sugar in **imported modules**.

```python
import latychain.ChainDotRule
```

### Transformation rules

| Source | Transformed to |
|--------|---------------|
| `.heading.h1` | `Chain(['heading', 'h1'])` |
| `.any(0).uuu` | `Chain([ChainRuleAtom.any(0), 'uuu'])` |
| `.any(0).uuu.rex(r'x\d')` | `Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])` |

**Rule**: segments without `()` → string; segments with `()` → `ChainRuleAtom.xxx()`.

### Safe skip list

The transformer ignores:

- String literals: `"hello .foo.bar"`
- Comments: `# .foo.bar`
- Float literals: `.5`, `.3e10`
- Object attributes: `obj.attr`, `func().attr`
- Index access: `list[0].attr`

### Limitations

- **Only transforms imported modules**, not the entry script itself.
- **Numeric segments (`.123`) not supported.** Use `Chain(['123'])`.
- **`.match()` is a Chain method**, not a RuleAtom. Call it on a separate variable.
