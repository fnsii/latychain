# API Reference

> **⚠️ Early Development** — API may change.

## Chain

```python
from latychain import Chain
```

### Construction

Standard explicit form:

```python
Chain(["a", "b", "c"])          # from a list
Chain(["a"])                    # single element
Chain()                         # empty chain
Chain([123])                    # number auto-converted to '123'
```

`/` shortcut (pathlib style):

```python
Chain / "a" / "b" / "c"         # → Chain(['a', 'b', 'c'])
Chain() / "a"                   # → Chain(['a'])
"a" / Chain(["b"])              # → Chain(['a', 'b'])
Chain(["a"]) / Chain(["b"])     # → Chain(['a', 'b'])
Chain / 1 / 2 / 3               # → Chain(['1', '2', '3'])
```

From dot-separated string (data only — cannot represent pattern atoms):

```python
Chain.from_str("a.b.c")        # → Chain(['a', 'b', 'c'])
Chain.from_str(".a.b.c")       # → Chain(['a', 'b', 'c'])
```

### Read operations

| Method | Returns | Description |
|--------|---------|-------------|
| `chain[i]` | `str \| ChainPatternAtom` | Indexed access (negative supported) |
| `chain[i:j]` | `Chain` | Slice returns a new Chain |
| `len(chain)` | `int` | Number of elements |
| `iter(chain)` | `Iterator` | Iterate over elements |
| `chain.elements` | `tuple` | Read-only underlying tuple |
| `"a" in chain` | `bool` | Membership test |

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

### Matching

```python
pattern.match(data)                    # Full-match backtracking
pattern.match(data, partial=True)      # Prefix match
pattern.to_list()                      # → list of elements
```

#### `match(data, partial=False)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `Chain` | — | Data chain to match against |
| `partial` | `bool` | `False` | If `True`, only match a prefix |

Returns `True` if the pattern matches the data.

---

## ChainPatternAtom

```python
from latychain import ChainPatternAtom              # full name
from latychain import ChainPatternAtom as Patom     # shortcut
```

`Patom` is just an alias — `Patom is ChainPatternAtom`.

### `any(min=1, max=-1)`

Match between `min` and `max` arbitrary elements. `max=-1` means unbounded.

| Example | Meaning |
|---------|---------|
| `ChainPatternAtom.any()` | At least 1 element |
| `ChainPatternAtom.any(0)` | 0 or more |
| `ChainPatternAtom.any(2)` | At least 2 |
| `ChainPatternAtom.any(1, 3)` | 1 to 3 |
| `ChainPatternAtom.any(0, 5)` | 0 to 5 |

Non-greedy with backtracking. `max=0` raises `ValueError`.

### `rex(pattern)`

Regex `fullmatch` on a **single** string element.

```python
ChainPatternAtom.rex(r'h[12]')     # matches 'h1', 'h2'
ChainPatternAtom.rex(r'\d+')       # matches '123', '0'
ChainPatternAtom.rex(r'x[0-9]')    # matches 'x0'..'x9'
```

### `enum(*alternatives)`

Pick **one** of several alternative chains. Strings are parsed via `Chain.from_str`.

```python
# Simple strings
ChainPatternAtom.enum('h1', 'h2', 'h3')

# Dot-separated strings
ChainPatternAtom.enum('type.h1', 'type.h2')

# Full chains
ChainPatternAtom.enum(
    Chain(["type", "h1"]),
    Chain(["type", "h2"]),
)
```

### `apply(func, count=1)`

Match `count` consecutive elements via a user-supplied predicate.

> **Note**: `apply` atoms compare by function **identity** (`is`), not value equality.
> Two equivalent but distinct lambdas are treated as different atoms.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `callable(Chain) -> bool` | — | Predicate receiving a Chain |
| `count` | `int` | `1` | Number of elements to pass to func |

```python
ChainPatternAtom.apply(lambda seg: str(seg).startswith('.x'))
ChainPatternAtom.apply(lambda seg: seg[0] != seg[1], count=2)
```

### `len(min, max=None)`

Constrain the **string length** of a single element.

```python
ChainPatternAtom.len(3)         # exactly 3: 'abc' ✓, 'ab' ✗
ChainPatternAtom.len(2, 5)      # 2 to 5 characters
```

### `un(value)`

Match any single element **not equal** to `value`.

```python
ChainPatternAtom.un('admin')     # matches 'user', 'guest'; not 'admin'
```

### `ext(chain)`

Optional segment: try matching `chain`, or skip (consume 0). Accepts `Chain`, `str`, or `ChainPatternAtom`.

```python
ChainPatternAtom.ext(Chain(["a"]))   # matches 'a' or skips
ChainPatternAtom.ext("a")            # matches 'a' or skips
ChainPatternAtom.ext("a.b")         # matches ['a','b'] or skips
ChainPatternAtom.ext(ChainPatternAtom.enum('x', 'y'))  # matches enum or skips
```

---

## `latychain.ChainDotRule`

Import hook that enables `.xxx.yyy` syntax sugar in **imported modules**.
Opt-in: only files with ``# useLatyChain`` in the first few lines are transformed.
``Chain`` and ``ChainPatternAtom`` are auto-injected into marked modules.

```python
import latychain.ChainDotRule
```

### Activation

Add ``# useLatyChain`` to the first few lines of each module that uses sugar syntax:

```python
# useLatyChain

data = .heading.h1          # → Chain(['heading', 'h1'])
rule = .any(0).uuu          # → Chain([ChainPatternAtom.any(0), 'uuu'])
```

No explicit ``from latychain import ...`` is needed in marked modules.

### Transformation rules

| Source | Transformed to |
|--------|---------------|
| `.heading.h1` | `Chain(['heading', 'h1'])` |
| `.any(0).uuu` | `Chain([ChainPatternAtom.any(0), 'uuu'])` |
| `.any(0).uuu.rex(r'x\d')` | `Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])` |

**Rule**: segments without `()` → string; segments with `()` → `ChainPatternAtom.xxx()`.

### Safe skip list

The transformer ignores:

- String literals: `"hello .foo.bar"`
- Comments: `# .foo.bar`
- Float literals: `.5`, `.3e10`
- Object attributes: `obj.attr`, `func().attr`

### Limitations

- **Only transforms imported modules**, not the entry script itself.
- **Requires ``# useLatyChain`` marker** in each file that uses the sugar.
- **Numeric segments at start (`.123`) not supported** — Python treats `.123` as float literal.
  Use `Chain(["123"])` instead. `.123.hi` also not supported (`.123` = float, `.hi` = attr access).
  Numeric segments after first position work: `.user.123` → `Chain(['user', '123'])`.
- **`.match()` is a Chain method**, not an atom method. Call it on a separate variable.
