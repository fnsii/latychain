# Usage Guide

> **⚠️ Early Development** — API may change.

## Installation

```bash
pip install latychain
```

Requires Python 3.10+.

---

## Two Construction Styles

### Standard: `Chain([...])`

Works everywhere, explicit, no magic:

```python
from latychain import Chain, ChainPatternAtom

data = Chain(["user", "profile", "123"])

rule = Chain([
    ChainPatternAtom.any(0),
    "user",
    ChainPatternAtom.any(0),
    ChainPatternAtom.rex(r"\d+"),
])

rule.match(data)   # True
```

### Shortcut: `import ... as Patom` + `/`

Shorter names, pathlib feel:

```python
from latychain import Chain, ChainPatternAtom as Patom

data = Chain / "user" / "profile" / "123"

rule = Chain / Patom.any(0) / "user" / Patom.any(0) / Patom.rex(r"\d+")

rule.match(data)   # True
```

### Sugar: `.xxx.yyy` (opt-in per module)

Requires a two-file setup + ``# useLatyChain`` marker:

**runner.py:**
```python
import latychain.ChainDotRule
import my_rules
```

**my_rules.py:**
```python
# useLatyChain

rule = .any(0).user.any(0).rex(r'\d+')
data = Chain.from_str('user.profile.123')
rule.match(data)     # True
```

> **Note**: The entry script itself cannot use `.xxx.yyy` syntax.

---

## Matching Deep Dive

### How matching works

`pattern.match(data)` walks both chains left-to-right:

| Data | Pattern | Match condition |
|------|---------|----------------|
| `'a'` | `'a'` | Exact string equality |
| `'a'` | `'b'` | Fail |
| `'5'` | `rex(r'\d')` | Regex fullmatch |
| `'x','y'` | `any(...)` | Non-greedy backtracking |
| `'b'` | `un('a')` | Negation (not equal) |
| `'abc'` | `len(2,4)` | String length in range |
| `'a','b'` | `ext(a),'b'` | Try match or skip |

### Backtracking example

```python
pattern = Chain([ChainPatternAtom.any(0), "uuu", ChainPatternAtom.rex(r"x\d")])
data = Chain(["pre", "uuu", "x1"])
pattern.match(data)
```

The engine tries:

1. `any=0`: skip nothing → `'uuu'` vs `'pre'` → fail, backtrack
2. `any=1`: consume `'pre'` → `'uuu'` matches → `rex(r'x\d')` matches `'x1'` → success!

### Full vs partial match

```python
data = Chain(["a", "b", "c", "d"])

Chain(["a", "b"]).match(data)                     # False
Chain(["a", "b"]).match(data, partial=True)       # True
Chain([ChainPatternAtom.any(0), "d"]).match(data)  # True
```

---

## Practical Patterns

### Configuration paths

```python
from latychain import Chain, ChainPatternAtom

rule = Chain(["config", "database", "connection", "pool", ChainPatternAtom.any(0)])

rule.match(Chain(["config", "database", "connection", "pool", "5"]))   # True
rule.match(Chain(["config", "database", "connection", "pool"]))        # True
rule.match(Chain(["config", "database", "timeout"]))                   # False
```

### Route permissions

```python
from latychain import Chain, ChainPatternAtom

rule = Chain(["api", "v1", ChainPatternAtom.enum(
    Chain(["users", ChainPatternAtom.any(0)]),
    Chain(["admin", ChainPatternAtom.un("secret"), ChainPatternAtom.any(0)]),
)])

rule.match(Chain(["api", "v1", "users", "123"]))              # True
rule.match(Chain(["api", "v1", "admin", "dashboard"]))        # True
rule.match(Chain(["api", "v1", "admin", "secret"]))            # False
rule.match(Chain(["api", "v2", "users", "123"]))               # False
```

### Log filtering

```python
from latychain import Chain, ChainPatternAtom

rule = Chain([
    ChainPatternAtom.rex(r"\d{4}"),
    ChainPatternAtom.rex(r"\d{2}"),
    ChainPatternAtom.rex(r"\d{2}"),
    ChainPatternAtom.enum(Chain(["ERROR"]), Chain(["CRITICAL"])),
    ChainPatternAtom.any(0),
])

rule.match(Chain(["2024", "01", "15", "ERROR", "timeout"]))      # True
rule.match(Chain(["2024", "01", "15", "INFO", "request"]))        # False
rule.match(Chain(["2024", "01", "15", "CRITICAL", "oom"]))        # True
```

### Optional features (ext)

```python
from latychain import Chain, ChainPatternAtom

rule = Chain(["item", ChainPatternAtom.rex(r"\d+"),
              ChainPatternAtom.ext(Chain(["details"]))])

rule.match(Chain(["item", "42"]))               # True (ext skipped)
rule.match(Chain(["item", "42", "details"]))    # True (ext matched)
rule.match(Chain(["item", "42", "extra"]))      # False
```

### Custom validation (apply)

```python
from latychain import Chain, ChainPatternAtom

rule = Chain(["user", ChainPatternAtom.rex(r"[a-z]+"), ChainPatternAtom.apply(
    lambda seg: int(str(seg).lstrip(".")) > 0
)])

rule.match(Chain(["user", "alice", "42"]))    # True
rule.match(Chain(["user", "alice", "0"]))      # False
rule.match(Chain(["user", "alice", "-1"]))     # False
```

---

## Using Chains as Dict Keys

```python
from latychain import Chain

perms = {
    Chain(["admin", "read"]):   True,
    Chain(["admin", "write"]):  True,
    Chain(["user",  "read"]):   True,
    Chain(["user",  "write"]):  False,
}

perms[Chain(["admin", "write"])]   # True
perms[Chain(["user",  "write"])]   # False
```

---

## `any` vs `ext`

| Feature | `any(min, max)` | `ext(chain)` |
|---------|----------------|--------------|
| What it matches | Any elements | A specific chain or nothing |
| Use case | Skip unknown content | Optional known structure |

```python
# any(0).b — any prefix works
Chain([ChainPatternAtom.any(0), "b"]).match(Chain(["a", "b"]))           # True
Chain([ChainPatternAtom.any(0), "b"]).match(Chain(["x", "y", "b"]))    # True
Chain([ChainPatternAtom.any(0), "b"]).match(Chain(["b"]))              # True

# .a.ext(.a).b — only .a.b or .a.a.b
pat = Chain(["a", ChainPatternAtom.ext(Chain(["a"])), "b"])
pat.match(Chain(["a", "b"]))                                            # True
pat.match(Chain(["a", "a", "b"]))                                       # True
pat.match(Chain(["a", "x", "b"]))                                       # False
```
