# latychain

**Immutable chain-structured data with backtracking pattern matching.**

```python
from latychain import Chain, ChainPatternAtom

# Chain([…]) — standard explicit construction
rule = Chain([ChainPatternAtom.any(0), "uuu", ChainPatternAtom.rex(r"x\d")])
data = Chain(["x", "uuu", "x1"])
rule.match(data)   # True
```

Two shortcuts: import `ChainPatternAtom as Patom`, and build with `/` instead of `[]`:

```python
from latychain import Chain, ChainPatternAtom as Patom

rule = Chain / Patom.any(0) / "uuu" / Patom.rex(r"x\d")
data = Chain / "x" / "uuu" / "x1"
rule.match(data)   # True
```

Plus compile-time `.xxx.yyy` sugar for opted-in modules:

```python
# useLatyChain
data = .heading.h1
rule = .any(0).uuu.rex(r"x\d")
rule.match(data)   # True
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

Elements are plain strings (data), numbers (auto-converted to str), or `ChainPatternAtom` instances (pattern rules). Hashable, usable as dict keys.

```python
c = Chain(["a", "b", "c"])
len(c)              # 3
c[0]                # 'a'
str(c)              # '.a.b.c'
c.to_list()         # ['a', 'b', 'c']
"b" in c            # True

# Numbers are auto-converted to strings
Chain([123])        # Chain(['123'])
Chain / 1 / 2 / 3   # Chain(['1', '2', '3'])

# Matching (backtracking, non-greedy) — pattern.match(data)
Chain(["a", "b"]).match(c)               # False — full match fails
Chain(["a", "b"]).match(c, partial=True) # True — prefix match

# pathlib-style / shortcut
Chain / "a" / "b" / "c"                  # same as Chain(["a","b","c"])

# Chain / Chain concatenation
Chain(["a", "b"]) / Chain(["c", "d"])    # Chain(["a","b","c","d"])

# From dot-separated string (data only — no pattern atoms)
Chain.from_str("a.b.c")                 # Chain(["a", "b", "c"])
Chain.from_str(".a.b.c")                # Chain(["a", "b", "c"])
```

### `ChainPatternAtom` — pattern atoms

| Factory | Matches |
|---------|---------|
| `any(min=1, max=-1)` | N arbitrary elements (`max=-1` = unbounded). Non-greedy. |
| `rex(pattern)` | Single element via regex `fullmatch` |
| `enum(*chains_or_strs)` | One of several alternative chains (strings auto-parsed via `from_str`) |
| `apply(func, count=1)` | Custom predicate receiving a `Chain` of `count` elements |
| `len(min, max=None)` | String length in `[min, max]` |
| `un(value)` | Any element not equal to `value` |
| `ext(chain)` | Optional segment — match or skip |

Import as `ChainPatternAtom` (full name) or `Patom` (shortcut):

```python
from latychain import Chain, ChainPatternAtom
# or
from latychain import Chain, ChainPatternAtom as Patom
```

```python
# any — between min and max arbitrary elements
rule = Chain([ChainPatternAtom.any(0), "yyy"])  # 0 or more before 'yyy'
rule.match(Chain(["x", "yyy"]))                 # True
rule.match(Chain(["yyy"]))                      # True

# rex — regex fullmatch on one element
Chain([ChainPatternAtom.rex(r"h[12]")]).match(Chain(["h1"]))    # True
Chain([ChainPatternAtom.rex(r"\d+")]).match(Chain(["123"]))     # True

# enum — pick one alternative (accepts Chain or string)
Chain([ChainPatternAtom.enum("user", "admin")]).match(Chain(["user"]))   # True
Chain([ChainPatternAtom.enum("type.h1", "type.h2")]).match(Chain(["type", "h1"]))  # True

rule = Chain([ChainPatternAtom.enum(
    Chain(["user", ChainPatternAtom.any(0)]),
    Chain(["admin", ChainPatternAtom.any(0)]),
)])
rule.match(Chain(["user", "login"]))   # True
rule.match(Chain(["guest"]))           # False

# ext — optional segment
rule = Chain(["a", ChainPatternAtom.ext(Chain(["pi"])), "b"])
rule.match(Chain(["a", "b"]))      # True — ext skipped
rule.match(Chain(["a", "pi", "b"])) # True — ext matched
rule.match(Chain(["a", "x", "b"]))  # False

# ext with enum
rule = Chain(["a", ChainPatternAtom.ext(ChainPatternAtom.enum("x", "y")), "b"])
rule.match(Chain(["a", "x", "b"]))  # True
rule.match(Chain(["a", "b"]))       # True — skipped

# apply — custom predicate
Chain([ChainPatternAtom.apply(lambda c: str(c).startswith(".x"))]).match(Chain(["xhello"]))  # True

# len — string length constraint
Chain([ChainPatternAtom.len(3)]).match(Chain(["abc"]))        # True
Chain([ChainPatternAtom.len(2, 5)]).match(Chain(["abc"]))     # True

# un — negation
Chain([ChainPatternAtom.un("admin")]).match(Chain(["user"]))   # True
```

All of the above can also be written with the `/` shortcut:

```python
from latychain import Chain, ChainPatternAtom as Patom

# any
rule = Chain / Patom.any(0) / "yyy"
rule.match(Chain / "x" / "yyy")                        # True

# rex
(Chain / Patom.rex(r"h[12]")).match(Chain / "h1")       # True

# enum
rule = Chain / Patom.enum(
    Chain / "user" / Patom.any(0),
    Chain / "admin" / Patom.any(0),
)
rule.match(Chain / "user" / "login")                   # True

# ext
rule = Chain / "a" / Patom.ext(Chain / "pi") / "b"
rule.match(Chain / "a" / "b")                          # True

# apply
rule = Chain / Patom.apply(lambda c: str(c).startswith(".x"))
rule.match(Chain / "xhello")                           # True

# len
(Chain / Patom.len(3)).match(Chain / "abc")             # True

# un
(Chain / Patom.un("admin")).match(Chain / "user")        # True
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
rule.match(x)                             # True

# Nested enum
rule2 = .any(0).enum(
    .admin.any(0),
    .user.any(0),
).rex(r'\d+')

rule2.match(Chain(["user", "login", "123"]))   # True

# Patom is auto-injected — use it with / for mixed styles
route = Chain / Patom.enum(
    Chain / "admin" / Patom.any(0),
    Chain / "user" / Patom.any(0),
) / Patom.rex(r"\d+")
route.match(Chain / "user" / "dashboard" / "42")  # True
```

The transformer skips strings, comments, float literals, and `obj.attr` access.
Only files with `# useLatyChain` are transformed — all other imports pass through untouched.

**Numeric segments at the start (`.123`) are not supported** — Python treats `.123` as a float literal.
Use `Chain(["123"])` instead. Numeric segments after the first position work: `.user.123` → `Chain(['user', '123'])`.
Note: `.123.hi` is also not supported (Python sees `.123` as float, then `.hi` as attribute access).

---

## Develop

```bash
git clone https://github.com/fnsii/latychain
cd latychain
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv run python test/run_all.py
```
