# API Reference

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
| `chain[i]` | `str \| ChainRuleAtom` | Indexed access (supports negative) |
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
| `hash(chain)` | `int` | Hashable (usable as dict key) |
| `bool(chain)` | `bool` | `True` if non-empty |

### Operations

```python
chain + other       # Concatenation → new Chain
chain.match(pattern, partial=False)   # Backtracking match
chain.startswith(prefix)              # Prefix check (partial match)
chain.to_list()                       # → list of elements
```

#### `match(pattern, partial=False)`

Check whether the data chain matches the given pattern.

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

### any

```python
ChainRuleAtom.any(min=0, max=0)
```

Match between `min` and `max` arbitrary elements. `max=0` means unbounded.

| Example | Meaning |
|---------|---------|
| `any()` | At least 1 element |
| `any(0)` | 0 or more |
| `any(2)` | At least 2 |
| `any(1, 3)` | 1 to 3 |
| `any(0, 5)` | 0 to 5 |

- Non-greedy; tries shortest matches first
- Backtracking: if a short match causes later pattern failure, tries longer

### rex

```python
ChainRuleAtom.rex(pattern)
```

Regex `fullmatch` on a **single** string element.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | `str` | Regex pattern (compiled with `re.compile`) |

```python
.rex(r'h[12]')     # matches 'h1', 'h2'
.rex(r'\d+')       # matches '123', '0'
.rex(r'x[0-9]')    # matches 'x0'..'x9'
```

### enum

```python
ChainRuleAtom.enum(*alternatives)
```

Pick **one** of several alternative chains.

| Parameter | Type | Description |
|-----------|------|-------------|
| `*alternatives` | `Chain` | One or more chains to try |

```python
.enum(
    Chain(['type', 'h1']),
    Chain(['type', 'h2']),
)
# matches .type.h1  or  .type.h2
```

### apply

```python
ChainRuleAtom.apply(func, long=1)
```

Match `long` consecutive elements via a user-supplied predicate.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `callable(Chain) -> bool` | — | Predicate receiving a Chain |
| `long` | `int` | `1` | Number of elements to pass to func |

```python
.apply(lambda seg: str(seg).startswith('.x'))
# single element starting with 'x'

.apply(lambda seg: len(seg) > 2, long=2)
# two consecutive elements, combined chain has length > 2
```

### long

```python
ChainRuleAtom.long(min, max=None)
```

Constrain the **string length** of a single element.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min` | `int` | — | Minimum length (inclusive) |
| `max` | `int \| None` | `None` | Maximum length; `None` = exact match with `min` |

```python
.long(3)          # exactly 3 characters: 'abc' ✓, 'ab' ✗
.long(2, 5)       # 2 to 5 characters
```

### un

```python
ChainRuleAtom.un(value)
```

Match any single element **not equal** to `value`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | Value to negate |

```python
.un('admin')      # matches 'user', 'guest'; does NOT match 'admin'
```

### ext

```python
ChainRuleAtom.ext(chain=None)
```

Optional segment: try matching `chain`, or skip (consume 0 elements).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chain` | `Chain \| None` | `None` | Optional chain to match |

```python
.ext()             # always skips (consumes 0)
.ext(Chain(['a'])) # matches 'a' or skips
```

---

## latychain.ChainDotRule

```python
import latychain.ChainDotRule
```

Import hook that enables `.xxx.yyy` syntax sugar. Registers a compile-time
transformer for all subsequently loaded modules.

### Transformation rules

| Source | Transformed to |
|--------|---------------|
| `.heading.h1` | `Chain(['heading', 'h1'])` |
| `.any(0).uuu` | `Chain([ChainRuleAtom.any(0), 'uuu'])` |
| `.any(0).uuu.rex(r'x\d')` | `Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])` |
| `.enum(.hi, .wuhu)` | `Chain([ChainRuleAtom.enum(Chain(['hi']), Chain(['wuhu']))])` |

**Rule**: segments without `()` → string; segments with `()` → `ChainRuleAtom.xxx()`.

### Safe skip list

The transformer correctly ignores:

- String literals: `"hello .foo.bar"`
- Comments: `# .foo.bar`
- Float literals: `.5`, `.3e10`
- Object attributes: `obj.attr`, `func().attr`
- Index access: `list[0].attr`
