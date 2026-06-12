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
```

`/` shortcut (pathlib style):

```python
Chain / "a" / "b" / "c"         # → Chain(['a', 'b', 'c'])
Chain() / "a"                   # → Chain(['a'])
"a" / Chain(["b"])              # → Chain(['a', 'b'])
```

### Read operations

| Method | Returns | Description |
|--------|---------|-------------|
| `chain[i]` | `str \| ChainPatternAtom` | Indexed access (negative supported) |
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
chain.match(pattern)                 # Full-match backtracking
chain.match(pattern, partial=True)   # Prefix match
chain.startswith(prefix)             # Same as partial match
chain.to_list()                      # → list of elements
```

#### `match(pattern, partial=False)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | `Chain` | — | Pattern chain (strings + atoms) |
| `partial` | `bool` | `False` | If `True`, only match a prefix |

Returns `True` if a match is found.

---

## ChainPatternAtom

```python
from latychain import ChainPatternAtom              # full name
from latychain import ChainPatternAtom as Patom     # shortcut
```

`Patom` is just an alias — `Patom is ChainPatternAtom`.

### `any(min=1, max=0)`

Match between `min` and `max` arbitrary elements. `max=0` means unbounded.

| Example | Meaning |
|---------|---------|
| `ChainPatternAtom.any()` | At least 1 element |
| `ChainPatternAtom.any(0)` | 0 or more |
| `ChainPatternAtom.any(2)` | At least 2 |
| `ChainPatternAtom.any(1, 3)` | 1 to 3 |
| `ChainPatternAtom.any(0, 5)` | 0 to 5 |

Non-greedy with backtracking.

### `rex(pattern)`

Regex `fullmatch` on a **single** string element.

```python
ChainPatternAtom.rex(r'h[12]')     # matches 'h1', 'h2'
ChainPatternAtom.rex(r'\d+')       # matches '123', '0'
ChainPatternAtom.rex(r'x[0-9]')    # matches 'x0'..'x9'
```

### `enum(*alternatives)`

Pick **one** of several alternative chains.

```python
pat = Chain([ChainPatternAtom.enum(
    Chain(["type", "h1"]),
    Chain(["type", "h2"]),
)])
# matches .type.h1 or .type.h2
```

### `apply(func, long=1)`

Match `long` consecutive elements via a user-supplied predicate.

> **Note**: `apply` atoms compare by function **identity** (`is`), not value equality.
> Two equivalent but distinct lambdas are treated as different atoms.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `callable(Chain) -> bool` | — | Predicate receiving a Chain |
| `long` | `int` | `1` | Number of elements to pass to func |

```python
ChainPatternAtom.apply(lambda seg: str(seg).startswith('.x'))
ChainPatternAtom.apply(lambda seg: seg[0] != seg[1], long=2)
```

### `long(min, max=None)`

Constrain the **string length** of a single element.

```python
ChainPatternAtom.long(3)         # exactly 3: 'abc' ✓, 'ab' ✗
ChainPatternAtom.long(2, 5)      # 2 to 5 characters
```

### `un(value)`

Match any single element **not equal** to `value`.

```python
ChainPatternAtom.un('admin')     # matches 'user', 'guest'; not 'admin'
```

### `ext(chain=None)`

Optional segment: try matching `chain`, or skip (consume 0).

```python
ChainPatternAtom.ext()               # always skips
ChainPatternAtom.ext(Chain(["a"]))   # matches 'a' or skips
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
- **Numeric segments (`.123`) not supported.** Use `Chain(["123"])`.
- **`.match()` is a Chain method**, not an atom method. Call it on a separate variable.
