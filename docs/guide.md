# Usage Guide

> **⚠️ Early Development** — API may change.

## Installation

```bash
pip install latychain
```

Requires Python 3.10+.

---

## Construction Styles

### Recommended: `/` shortcut with `Patom`

```python
from latychain import Chain, ChainPatternAtom as Patom

data = Chain / "user" / "profile" / "123"
rule = Chain / Patom.any(0) / "user" / Patom.any(0) / Patom.rex(r"\d+")

rule.match(data)   # True
```

### Standard: `Chain([...])`

```python
from latychain import Chain, ChainPatternAtom as Patom

data = Chain(["user", "profile", "123"])
rule = Chain([Patom.any(0), "user", Patom.any(0), Patom.rex(r"\d+")])

rule.match(data)   # True
```

### Sugar: `.xxx.yyy` (opt-in per module)

```python
# runner.py
import latychain.ChainDotRule
import my_rules

# my_rules.py
# useLatyChain
rule = .any(0).user.any(0).rex(r'\d+')
data = Chain / "user" / "profile" / "123"
rule.match(data)   # True
```

---

## Matching

### How it works

`pattern.match(data)` walks both chains left-to-right:

| Data | Pattern | Match condition |
|------|---------|----------------|
| `'a'` | `'a'` | Exact string equality |
| `'5'` | `rex(r'\d')` | Regex fullmatch |
| `'x','y'` | `any(...)` | Non-greedy backtracking |
| `'b'` | `un('a')` | Negation (not equal) |
| `'abc'` | `len(2,4)` | String length in range |
| `'a','b'` | `ext(a),'b'` | Try match or skip |

### Backtracking

```python
rule = Chain / Patom.any(0) / "uuu" / Patom.rex(r"x\d")
data = Chain / "pre" / "uuu" / "x1"

rule.match(data)   # True
```

The engine tries:
1. `any=0`: skip nothing → `'uuu'` vs `'pre'` → fail, backtrack
2. `any=1`: consume `'pre'` → `'uuu'` matches → `rex` matches `'x1'` → success

### Full vs Partial

```python
data = Chain / "a" / "b" / "c" / "d"

Chain(["a", "b"]).match(data)                     # False
Chain(["a", "b"]).match(data, partial=True)       # True
Chain([Patom.any(0), "d"]).match(data)            # True
```

---

## Practical Patterns

### Configuration Paths

```python
from latychain import Chain, ChainPatternAtom as Patom

rule = Chain / "config" / "database" / "connection" / "pool" / Patom.any(0)

rule.match(Chain / "config" / "database" / "connection" / "pool" / "5")   # True
rule.match(Chain / "config" / "database" / "timeout")                     # False
```

### Route Permissions

```python
from latychain import Chain, ChainPatternAtom as Patom

rule = Chain / "api" / "v1" / Patom.enum(
    Chain / "users" / Patom.any(0),
    Chain / "admin" / Patom.un("secret") / Patom.any(0),
)

rule.match(Chain / "api" / "v1" / "users" / "123")           # True
rule.match(Chain / "api" / "v1" / "admin" / "dashboard")     # True
rule.match(Chain / "api" / "v1" / "admin" / "secret")        # False
```

### Log Filtering

```python
from latychain import Chain, ChainPatternAtom as Patom

rule = (
    Chain / Patom.rex(r"\d{4}") / Patom.rex(r"\d{2}") / Patom.rex(r"\d{2}")
    / Patom.enum("ERROR", "CRITICAL")
    / Patom.any(0)
)

rule.match(Chain / "2024" / "01" / "15" / "ERROR" / "timeout")     # True
rule.match(Chain / "2024" / "01" / "15" / "INFO" / "request")      # False
rule.match(Chain / "2024" / "01" / "15" / "CRITICAL" / "oom")      # True
```

### Optional Features

```python
from latychain import Chain, ChainPatternAtom as Patom

rule = Chain / "item" / Patom.rex(r"\d+") / Patom.ext("details")

rule.match(Chain / "item" / "42")                 # True (ext skipped)
rule.match(Chain / "item" / "42" / "details")     # True (ext matched)
rule.match(Chain / "item" / "42" / "extra")        # False
```

### Custom Validation

```python
from latychain import Chain, ChainPatternAtom as Patom

rule = Chain / "user" / Patom.rex(r"[a-z]+") / Patom.apply(
    lambda seg: int(str(seg).lstrip(".")) > 0
)

rule.match(Chain / "user" / "alice" / "42")    # True
rule.match(Chain / "user" / "alice" / "0")     # False
```

---

## Dict Keys

```python
from latychain import Chain

perms = {
    Chain / "admin" / "read":   True,
    Chain / "admin" / "write":  True,
    Chain / "user" / "read":    True,
    Chain / "user" / "write":   False,
}

perms[Chain / "admin" / "write"]   # True
perms[Chain / "user" / "write"]    # False
```

---

## `any` vs `ext`

| Feature | `any(min, max)` | `ext(chain)` |
|---------|----------------|--------------|
| Matches | Any elements | Specific chain or nothing |
| Use case | Skip unknown content | Optional known structure |

```python
# any(0).b — matches any prefix before 'b'
Chain([Patom.any(0), "b"]).match(Chain / "x" / "y" / "b")  # True
Chain([Patom.any(0), "b"]).match(Chain / "b")               # True

# ext(.a).b — only matches 'a' or nothing before 'b'
rule = Chain / "a" / Patom.ext("a") / "b"
rule.match(Chain / "a" / "b")                               # True
rule.match(Chain / "a" / "a" / "b")                         # True
rule.match(Chain / "a" / "x" / "b")                         # False
```
