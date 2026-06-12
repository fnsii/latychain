# latychain

**Immutable chain-structured data with backtracking pattern matching.**

```python
from latychain import Chain, ChainPatternAtom as Patom

# Build chains with / shortcut
rule = Chain / Patom.any(0) / "uuu" / Patom.rex(r"x\d")
data = Chain / "x" / "uuu" / "x1"

# Pattern matching: pattern.match(data)
rule.match(data)   # True
```

---

## Install

```bash
pip install latychain
```

Python 3.10+.

---

## Quick Start

### Construction

```python
from latychain import Chain, ChainPatternAtom as Patom

# pathlib-style with /
Chain / "a" / "b" / "c"              # Chain(['a', 'b', 'c'])
Chain / 1 / 2 / 3                    # Chain(['1', '2', '3']) — numbers auto-converted

# Standard list constructor
Chain(["a", "b", "c"])               # same result

# From dot-separated string (data only)
Chain.from_str("a.b.c")             # Chain(['a', 'b', 'c'])

# Chain concatenation
(Chain / "a" / "b") / (Chain / "c")  # Chain(['a', 'b', 'c'])
```

### Matching

```python
from latychain import Chain, ChainPatternAtom as Patom

# pattern.match(data) — returns True/False
Chain([Patom.any(0), "b"]).match(Chain / "a" / "b")      # True
Chain([Patom.len(3)]).match(Chain / "abc")                # True
Chain([Patom.un("admin")]).match(Chain / "user")          # True

# Partial match (prefix)
Chain(["a", "b"]).match(Chain / "a" / "b" / "c", partial=True)  # True
```

---

## Pattern Atoms

| Factory | Matches |
|---------|---------|
| `Patom.any(min=1, max=-1)` | N arbitrary elements (`max=-1` = unbounded) |
| `Patom.rex(pattern)` | Single element via regex `fullmatch` |
| `Patom.enum(*args)` | One of several alternatives (strings auto-parsed via `from_str`) |
| `Patom.apply(func, count=1)` | Custom predicate on `count` elements |
| `Patom.len(min, max=None)` | String length in `[min, max]` |
| `Patom.un(value)` | Any element not equal to `value` |
| `Patom.ext(chain)` | Optional segment — match or skip |

### Examples

```python
from latychain import Chain, ChainPatternAtom as Patom

# any — match N elements
Chain([Patom.any(0), "end"]).match(Chain / "x" / "y" / "end")  # True
Chain([Patom.any(2), "z"]).match(Chain / "x" / "y" / "z")      # True

# rex — regex match
Chain([Patom.rex(r"h[12]")]).match(Chain / "h1")                # True
Chain([Patom.rex(r"\d+")]).match(Chain / "123")                 # True

# enum — pick one (accepts strings or Chains)
Chain([Patom.enum("user", "admin")]).match(Chain / "user")      # True
Chain([Patom.enum("type.h1", "type.h2")]).match(Chain / "type" / "h1")  # True

# ext — optional segment
rule = Chain / "a" / Patom.ext(Chain / "pi") / "b"
rule.match(Chain / "a" / "b")                                   # True (skipped)
rule.match(Chain / "a" / "pi" / "b")                            # True (matched)

# ext with enum
rule = Chain / "a" / Patom.ext(Patom.enum("x", "y")) / "b"
rule.match(Chain / "a" / "x" / "b")                             # True

# apply — custom predicate
# func receives a Chain of `count` elements (default 1)
# str(chain) returns dot-separated representation
Chain([Patom.apply(lambda c: str(c).startswith(".x"))]).match(Chain / "xhello")  # True
Chain([Patom.apply(lambda c: c[0] != c[1], count=2)]).match(Chain / "a" / "b")  # True

# len — string length
Chain([Patom.len(3)]).match(Chain / "abc")                      # True
Chain([Patom.len(2, 5)]).match(Chain / "abc")                   # True

# un — negation
Chain([Patom.un("admin")]).match(Chain / "user")                # True
```

---

## `.xxx.yyy` Syntax Sugar

An import hook transforms `.xxx.yyy` expressions into `Chain([...])` calls at compile time.
**Opt-in per module** — add `# useLatyChain` marker.

**runner.py** (entry point — no sugar here):
```python
import latychain.ChainDotRule   # registers the hook
import my_code                   # this file gets transformed
```

**my_code.py** (uses sugar):
```python
# useLatyChain

data = .heading.h1                       # → Chain(['heading', 'h1'])
rule = .any(0).uuu.rex(r'x\d')          # → Chain([Patom.any(0), 'uuu', Patom.rex(...)])

rule.match(data)                          # True

# Nested atoms
rule2 = .any(0).enum(
    .admin.any(0),
    .user.any(0),
).rex(r'\d+')

# Mix with Patom
route = Chain / Patom.enum(
    Chain / "admin" / Patom.any(0),
    Chain / "user" / Patom.any(0),
) / Patom.rex(r"\d+")
```

### Limitations

- Only transforms **imported modules**, not the entry script
- Requires `# useLatyChain` marker in each file
- `.123` at start not supported (Python float literal)
- `.match()` is a Chain method, call on separate variable

---

## Chain API

| Method | Description |
|--------|-------------|
| `chain[i]` | Element access (negative indexing supported) |
| `chain[i:j]` | Slice returns new Chain |
| `len(chain)` | Number of elements |
| `chain.to_list()` | Convert to list |
| `"x" in chain` | Membership test |
| `str(chain)` | Dot-separated string (`.a.b.c`) |
| `Chain.from_str(s)` | Parse dot-separated string |
| `chain / "x"` | Append element |
| `chain1 / chain2` | Concatenate chains |
| `pattern.match(data)` | Backtracking match |
| `pattern.match(data, partial=True)` | Prefix match |

---

## Develop

```bash
git clone https://github.com/fnsii/latychain
cd latychain
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv run python test/run_all.py
```
