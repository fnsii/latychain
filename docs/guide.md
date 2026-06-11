# Usage Guide

> **⚠️ 早期开发阶段** — API 可能发生变化。

## Installation

```bash
pip install latychain
```

Requires Python 3.10+.

---

## Two Ways to Build Chains

### 1. Explicit construction (works everywhere)

No imports or setup needed beyond `from latychain import Chain, ChainRuleAtom`:

```python
from latychain import Chain, ChainRuleAtom

# Data chain
data = Chain(['user', 'profile', 'avatar'])

# Rule chain
rule = Chain([
    ChainRuleAtom.any(0),
    'user',
    ChainRuleAtom.any(0),
    ChainRuleAtom.rex(r'\d+'),
])

# Match
data.match(rule)
```

### 2. `.xxx.yyy` syntax sugar (recommended for readability)

Register the import hook once at your entry point, then use `.xxx.yyy` everywhere:

```python
# entry_point.py
import latychain.ChainDotRule   # do this once

# any_module.py
from latychain import Chain

# Data chains
user_path = .user.profile.avatar
heading = .heading.h1

# Rule chains
rule = .any(0).user.any(0).rex(r'\d+')

# Matching (call .match() on a Chain variable, not in the chain expression)
Chain(['user', 'profile', '123']).match(rule)    # True
Chain(['guest', 'login']).match(rule)             # False
```

The hook automatically transforms `.xxx` at **compile time** (no runtime overhead).

---

## Matching Deep Dive

### How matching works

`data.match(pattern)` walks both chains left-to-right, element by element:

| Data element | Pattern element | Match condition |
|-------------|-----------------|-----------------|
| `'a'` | `'a'` | Exact string equality |
| `'a'` | `'b'` | Fail |
| `'a'` | `rex(r'\d')` | Regex fullmatch |
| `'a'` | `any(...)` | Non-greedy backtracking |
| `'a'` | `un('a')` | Negation (not equal) |
| `'a'` | `long(2,4)` | String length in range |
| `'a'` | `ext(Chain(['a']))` | Try match, or skip |

### Backtracking example

```python
rule = .any(0).uuu.rex(r'x\d')
data = .pre.uuu.x1
```

The engine tries:

1. `any=0`: skip nothing → next expects `'uuu'` at position 0, but sees `'pre'` → **fail, backtrack**
2. `any=1`: consume `'pre'` → next expects `'uuu'` at position 1, sees `'uuu'` → **match** → next expects `rex(r'x\d')` at position 2, sees `'x1'` → **match** → **success!**

### Full vs partial match

```python
data = .a.b.c.d

data.match(.a.b)               # False — pattern only consumes a,b, leaving c,d
data.match(.a.b, partial=True) # True  — prefix matched
data.match(.any(0).d)          # True  — any consumes a,b,c, then d matches
```

---

## Practical Patterns

### Configuration paths

```python
import latychain.ChainDotRule

rule = .config.database.connection.pool.any(0)

Chain(['config', 'database', 'connection', 'pool', '5']).match(rule)  # True
Chain(['config', 'database', 'connection', 'pool']).match(rule)       # True
Chain(['config', 'database', 'timeout']).match(rule)                  # False
```

### Routing / permissions

```python
import latychain.ChainDotRule

# Allow /api/v1/users/* and /api/v1/admin/* but not /api/v1/admin/secret
route_rule = .api.v1.enum(
    .users.any(0),
    .admin.un('secret').any(0)
)

Chain(['api', 'v1', 'users', '123']).match(route_rule)              # True
Chain(['api', 'v1', 'admin', 'dashboard']).match(route_rule)        # True
Chain(['api', 'v1', 'admin', 'secret']).match(route_rule)            # False
Chain(['api', 'v2', 'users', '123']).match(route_rule)               # False
```

### Log level filtering

```python
import latychain.ChainDotRule

# Match error/critical logs with timestamps
log_rule = (
    .rex(r'\d{4}')      # year
    .rex(r'\d{2}')      # month
    .rex(r'\d{2}')      # day
    .enum(
        .ERROR,
        .CRITICAL
    )
    .any(0)
)

Chain(['2024', '01', '15', 'ERROR', 'timeout']).match(log_rule)      # True
Chain(['2024', '01', '15', 'INFO', 'request']).match(log_rule)        # False
Chain(['2024', '01', '15', 'CRITICAL', 'oom']).match(log_rule)        # True
```

### Optional features (ext)

```python
import latychain.ChainDotRule

# .item.<id> optionally followed by .details
rule = .item.rex(r'\d+').ext(.details)

Chain(['item', '42']).match(rule)              # True (ext skipped)
Chain(['item', '42', 'details']).match(rule)   # True (ext matched)
Chain(['item', '42', 'extra']).match(rule)     # False (ext only accepts .details)
```

### Custom validation (apply)

```python
import latychain.ChainDotRule

# IDs must be positive integers
rule = .user.rex(r'[a-z]+').apply(
    lambda seg: int(str(seg).lstrip('.')) > 0
)

Chain(['user', 'alice', '42']).match(rule)    # True
Chain(['user', 'alice', '0']).match(rule)      # False (not > 0)
Chain(['user', 'alice', '-1']).match(rule)     # False
```

---

## Using Chains as Dictionary Keys

Because chains are immutable and hashable:

```python
from latychain import Chain

permissions = {
    Chain(['admin', 'read']): True,
    Chain(['admin', 'write']): True,
    Chain(['user', 'read']): True,
    Chain(['user', 'write']): False,
}

permissions[Chain(['admin', 'write'])]   # True
permissions[Chain(['user', 'write'])]    # False
```

---

## Comparing `any` and `ext`

Both match optional content, but differ in **how** they match:

| Feature | `any(min, max)` | `ext(chain)` |
|---------|----------------|--------------|
| What it matches | Any elements (unconstrained) | A specific chain or nothing |
| Use case | Skip unknown content | Optional known structure |
| Example | `.any(0).end` matches everything up to `.end` | `.a.ext(.b).c` matches `.a.c` or `.a.b.c` |

```python
.any(0).b     # .a.b, .x.y.b, .b — any prefix allowed
.ext(.a).b    # .a.b or .b only — no .x.y.b
```

---

## Migrating from Explicit to Sugar

Before (explicit):

```python
from latychain import Chain, ChainRuleAtom

data = Chain(['user', 'profile'])
rule = Chain([ChainRuleAtom.any(0), 'admin'])
```

After (sugar):

```python
import latychain.ChainDotRule

data = .user.profile
rule = .any(0).admin
```

You can mix both styles freely — the hook only transforms `.xxx` at the source level.

---

## Known Limitations

- **`.match()` is a Chain method, not a chain segment.** Always call `.match()` on a separate Chain variable:
  ```python
  # ✅ Correct
  data = .user.login.id123
  data.match(rule)
  ```

- **Numeric-only segments (`.123`) are not supported.** Use `Chain(['123'])` for numeric data.

- **The import hook only transforms modules imported after it.** The entry-point script itself is not transformed.
