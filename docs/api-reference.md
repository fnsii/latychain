# API Reference

> **⚠️ Early Development** — API may change.

## Chain

```python
from latychain import Chain, ChainPatternAtom as Patom
```

### Construction

```python
Chain(["a", "b", "c"])          # from list
Chain(["a"])                    # single element
Chain()                         # empty chain
Chain([123])                    # number auto-converted to '123'

Chain / "a" / "b" / "c"         # pathlib-style shortcut
Chain / 1 / 2 / 3               # numbers auto-converted

"a" / Chain(["b"])              # prepend
Chain(["a"]) / Chain(["b"])     # concatenate

Chain.from_str("a.b.c")        # from dot-separated string
Chain.from_str(".a.b.c")       # leading dot ignored
```

### Read Operations

| Method | Returns | Description |
|--------|---------|-------------|
| `chain[i]` | `str \| Patom` | Indexed access (negative supported) |
| `chain[i:j]` | `Chain` | Slice returns new Chain |
| `len(chain)` | `int` | Number of elements |
| `iter(chain)` | `Iterator` | Iterate over elements |
| `chain.elements` | `tuple` | Read-only underlying tuple |
| `"a" in chain` | `bool` | Membership test |

### String Representation

| Method | Returns | Example |
|--------|---------|---------|
| `str(chain)` | `str` | `".a.b.c"` |
| `repr(chain)` | `str` | `"Chain(['a', 'b', 'c'])"` |

### Value Semantics

| Method | Returns | Description |
|--------|---------|-------------|
| `chain == other` | `bool` | Value equality |
| `hash(chain)` | `int` | Hashable (dict key) |
| `bool(chain)` | `bool` | `True` if non-empty |

### Matching

```python
pattern.match(data)                    # Full-match backtracking
pattern.match(data, partial=True)      # Prefix match
pattern.to_list()                      # → list of elements
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `Chain` | — | Data chain to match against |
| `partial` | `bool` | `False` | If `True`, only match a prefix |

Returns `True` if the pattern matches the data.

---

## ChainPatternAtom (Patom)

```python
from latychain import Chain, ChainPatternAtom as Patom
```

`Patom` is a shorthand alias — `Patom is ChainPatternAtom`.

### `any(min=1, max=-1)`

Match between `min` and `max` arbitrary elements. `max=-1` means unbounded.

| Example | Meaning |
|---------|---------|
| `Patom.any()` | At least 1 element |
| `Patom.any(0)` | 0 or more |
| `Patom.any(2)` | At least 2 |
| `Patom.any(1, 3)` | 1 to 3 |

Non-greedy with backtracking. `max=0` raises `ValueError`.

### `rex(pattern)`

Regex `fullmatch` on a single string element.

```python
Patom.rex(r'h[12]')     # matches 'h1', 'h2'
Patom.rex(r'\d+')       # matches '123', '0'
```

### `enum(*alternatives)`

Pick one of several alternatives. Strings are parsed via `Chain.from_str`.

```python
Patom.enum('h1', 'h2', 'h3')              # simple strings
Patom.enum('type.h1', 'type.h2')          # dot-separated
Patom.enum(Chain / "a", Chain / "b")      # full chains
```

### `apply(func, count=1)`

Match `count` consecutive elements via a user-supplied predicate.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `callable(Chain) -> bool` | — | Predicate receiving a Chain |
| `count` | `int` | `1` | Number of elements to pass to func |

```python
Patom.apply(lambda seg: str(seg).startswith('.x'))
Patom.apply(lambda seg: seg[0] != seg[1], count=2)
```

> **Note**: `apply` atoms compare by function **identity** (`is`), not value equality.

### `len(min, max=None)`

Constrain the string length of a single element.

```python
Patom.len(3)         # exactly 3 characters
Patom.len(2, 5)      # 2 to 5 characters
```

### `un(value)`

Match any single element not equal to `value`.

```python
Patom.un('admin')    # matches 'user', 'guest'; not 'admin'
```

### `ext(chain)`

Optional segment: try matching `chain`, or skip (consume 0).

```python
Patom.ext(Chain / "a")              # matches 'a' or skips
Patom.ext("a")                      # matches 'a' or skips
Patom.ext("a.b")                    # matches ['a','b'] or skips
Patom.ext(Patom.enum('x', 'y'))     # matches enum or skips
```

---

## Sugar Syntax (`.xxx.yyy`)

Import hook that enables `.xxx.yyy` syntax in imported modules.

```python
import latychain.ChainDotRule   # registers the hook
```

### Activation

Add `# useLatyChain` to the first few lines of each module:

```python
# useLatyChain

data = .heading.h1          # → Chain(['heading', 'h1'])
rule = .any(0).uuu          # → Chain([Patom.any(0), 'uuu'])
```

### Transformation Rules

| Source | Transformed to |
|--------|---------------|
| `.heading.h1` | `Chain(['heading', 'h1'])` |
| `.any(0).uuu` | `Chain([Patom.any(0), 'uuu'])` |
| `.user.123` | `Chain(['user', '123'])` |

Segments without `()` → string; segments with `()` → `Patom.xxx()`.

### Limitations

- Only transforms **imported modules**, not entry script
- Requires `# useLatyChain` marker
- `.123` at start not supported (Python float literal)
- `.match()` is a Chain method, call on separate variable
