# latychain

**Immutable chain-structured data with backtracking pattern matching.**

```python
from latychain import Chain, ChainPatternAtom

# Chain([…]) — standard explicit construction
rule = Chain([ChainPatternAtom.any(0), "uuu", ChainPatternAtom.rex(r"x\d")])
data = Chain(["x", "uuu", "x1"])
data.match(rule)   # True
```

Two shortcuts: import `ChainPatternAtom as Patom`, and build with `/` instead of `[]`:

```python
from latychain import Chain, ChainPatternAtom as Patom

rule = Chain / Patom.any(0) / "uuu" / Patom.rex(r"x\d")
data = Chain / "x" / "uuu" / "x1"
data.match(rule)   # True
```

Plus compile-time `.xxx.yyy` sugar for opted-in modules:

```python
# useLatyChain
data = .heading.h1
rule = .any(0).uuu.rex(r"x\d")
data.match(rule)   # True
```

---

## Install

```bash
pip install latychain
```

Python 3.10+.

---

## Core concepts

### `Chain` — immutable ordered container

Elements are plain strings (data) or `ChainPatternAtom` instances (pattern rules). Hashable, usable as dict keys.

```python
c = Chain(["a", "b", "c"])
len(c)              # 3
c[0]                # 'a'
str(c)              # '.a.b.c'
c.to_list()         # ['a', 'b', 'c']
"b" in c            # True

# Matching (backtracking, non-greedy)
c.match(Chain(["a", "b"]))               # False — full match fails
c.match(Chain(["a", "b"]), partial=True) # True — prefix match
c.startswith(Chain(["a", "b"]))          # True — same as partial

# pathlib-style / shortcut
Chain / "a" / "b" / "c"                  # same as Chain(["a","b","c"])
```

### `ChainPatternAtom` — pattern atoms

| Factory | Matches |
|---------|---------|
| `any(min=1, max=0)` | N arbitrary elements (`max=0` = unbounded). Non-greedy. |
| `rex(pattern)` | Single element via regex `fullmatch` |
| `enum(*chains)` | One of several alternative chains |
| `apply(func, long=1)` | Custom predicate receiving a `Chain` of `long` elements |
| `long(min, max=None)` | String length in `[min, max]` |
| `un(value)` | Any element not equal to `value` |
| `ext(chain=None)` | Optional segment — match or skip |

Import as `ChainPatternAtom` (full name) or `Patom` (shortcut):

```python
from latychain import Chain, ChainPatternAtom
# or
from latychain import Chain, ChainPatternAtom as Patom
```

```python
# any — between min and max arbitrary elements
rule = Chain([ChainPatternAtom.any(0), "yyy"])  # 0 or more before 'yyy'
Chain(["x", "yyy"]).match(rule)                 # True
Chain(["yyy"]).match(rule)                      # True

# rex — regex fullmatch on one element
Chain(["h1"]).match(Chain([ChainPatternAtom.rex(r"h[12]")]))    # True
Chain(["123"]).match(Chain([ChainPatternAtom.rex(r"\d+")]))     # True

# enum — pick one alternative
rule = Chain([ChainPatternAtom.enum(
    Chain(["user", ChainPatternAtom.any(0)]),
    Chain(["admin", ChainPatternAtom.any(0)]),
)])
Chain(["user", "login"]).match(rule)   # True
Chain(["guest"]).match(rule)           # False

# ext — optional segment
rule = Chain(["a", ChainPatternAtom.ext(Chain(["pi"])), "b"])
Chain(["a", "b"]).match(rule)      # True — ext skipped
Chain(["a", "pi", "b"]).match(rule) # True — ext matched
Chain(["a", "x", "b"]).match(rule)  # False

# apply — custom predicate
rule = Chain([ChainPatternAtom.apply(lambda c: str(c).startswith(".x"))])
Chain(["xhello"]).match(rule)   # True

# long — string length constraint
Chain(["abc"]).match(Chain([ChainPatternAtom.long(3)]))        # True
Chain(["abc"]).match(Chain([ChainPatternAtom.long(2, 5)]))     # True

# un — negation
Chain(["user"]).match(Chain([ChainPatternAtom.un("admin")]))   # True
```

All of the above can also be written with the `/` shortcut:

```python
from latychain import Chain, ChainPatternAtom as Patom

# any
rule = Chain / Patom.any(0) / "yyy"
(Chain / "x" / "yyy").match(rule)                        # True

# rex
(Chain / "h1").match(Chain / Patom.rex(r"h[12]"))       # True

# enum
rule = Chain / Patom.enum(
    Chain / "user" / Patom.any(0),
    Chain / "admin" / Patom.any(0),
)
(Chain / "user" / "login").match(rule)                   # True

# ext
rule = Chain / "a" / Patom.ext(Chain / "pi") / "b"
(Chain / "a" / "b").match(rule)                          # True

# apply
rule = Chain / Patom.apply(lambda c: str(c).startswith(".x"))
(Chain / "xhello").match(rule)                           # True

# long
(Chain / "abc").match(Chain / Patom.long(3))             # True

# un
(Chain / "user").match(Chain / Patom.un("admin"))        # True
```

---

## `.xxx.yyy` syntax sugar

An import hook transforms `.xxx.yyy` expressions into `Chain([...])` calls at compile time.
**Opt-in per module** — add `# useLatyChain` to the first few lines. `Chain`, `ChainPatternAtom`,
and the `Patom` shortcut are auto-injected, no explicit import needed.

**Requires two files** — the hook only transforms imported modules, not the entry script:

**runner.py** (no sugar):
```python
import latychain.ChainDotRule   # registers the hook
import my_code                   # this file gets transformed
```

**my_code.py** (uses sugar):
```python
# useLatyChain

# Segments without () → strings; with () → ChainPatternAtom.xxx()
data = .heading.h1                       # → Chain(['heading', 'h1'])
rule = .any(0).uuu.rex(r'x\d')

x = .x.uuu.x1
x.match(rule)                             # True

# Nested enum
rule2 = .any(0).enum(
    .admin.any(0),
    .user.any(0),
).rex(r'\d+')

Chain(["user", "login", "123"]).match(rule2)   # True

# Patom is auto-injected — use it with / for mixed styles
route = Chain / Patom.enum(
    Chain / "admin" / Patom.any(0),
    Chain / "user" / Patom.any(0),
) / Patom.rex(r"\d+")
(Chain / "user" / "dashboard" / "42").match(route)  # True
```

The transformer skips strings, comments, float literals, and `obj.attr` access.
Only files with `# useLatyChain` are transformed — all other imports pass through untouched.

**Numeric segments (`.123`) are not supported** — use `Chain(["123"])` instead.

---

## Develop

```bash
git clone https://github.com/fnsii/latychain
cd latychain
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv run python test/run_all.py
```
