# Usage Guide

> **⚠️ Early Development** — API may change.

## Installation

```bash
pip install latychain
```

Requires Python 3.10+.

---

## Two Ways to Use latychain

### 1. Explicit API (recommended for most code)

Works in any `.py` file, no setup needed:

```python
from latychain import Chain, ChainRuleAtom

data = Chain(['user', 'profile', 'avatar'])

rule = Chain([
    ChainRuleAtom.any(0),
    'user',
    ChainRuleAtom.any(0),
    ChainRuleAtom.rex(r'\d+'),
])

data.match(rule)
```

### 2. `.xxx.yyy` sugar (for readability in suffix modules)

Requires a two-file setup. The entry script registers the hook, then imports modules that use the sugar:

**runner.py:**
```python
import latychain.ChainDotRule
import my_rules      # this module uses .xxx.yyy syntax
```

**my_rules.py:**
```python
from latychain import Chain

rule = .any(0).user.any(0).rex(r'\d+')
data = .user.profile.id123
data.match(rule)     # True
```

> **Note**: The entry script (runner) itself cannot use `.xxx.yyy` syntax.

---

## Matching Deep Dive

### How matching works

`data.match(pattern)` walks both chains left-to-right:

| Data | Pattern | Match condition |
|------|---------|----------------|
| `'a'` | `'a'` | Exact string equality |
| `'a'` | `'b'` | Fail |
| `'5'` | `rex(r'\d')` | Regex fullmatch |
| `'x','y'` | `any(...)` | Non-greedy backtracking |
| `'b'` | `un('a')` | Negation (not equal) |
| `'abc'` | `long(2,4)` | String length in range |
| `'a','b'` | `ext(a),'b'` | Try match or skip |

### Backtracking example

```python
pattern = Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])
data = Chain(['pre', 'uuu', 'x1'])
data.match(pattern)
```

The engine tries:

1. `any=0`: skip nothing → `'uuu'` vs `'pre'` → fail, backtrack
2. `any=1`: consume `'pre'` → `'uuu'` matches → `rex(r'x\d')` matches `'x1'` → success!

### Full vs partial match

```python
data = Chain(['a', 'b', 'c', 'd'])

data.match(Chain(['a', 'b']))                    # False
data.match(Chain(['a', 'b']), partial=True)      # True
data.match(Chain([ChainRuleAtom.any(0), 'd']))   # True
```

---

## Practical Patterns

### Configuration paths

```python
from latychain import Chain, ChainRuleAtom

rule = Chain(['config', 'database', 'connection', 'pool', ChainRuleAtom.any(0)])

Chain(['config', 'database', 'connection', 'pool', '5']).match(rule)   # True
Chain(['config', 'database', 'connection', 'pool']).match(rule)        # True
Chain(['config', 'database', 'timeout']).match(rule)                   # False
```

### Route permissions

```python
from latychain import Chain, ChainRuleAtom

rule = Chain(['api', 'v1', ChainRuleAtom.enum(
    Chain(['users', ChainRuleAtom.any(0)]),
    Chain(['admin', ChainRuleAtom.un('secret'), ChainRuleAtom.any(0)]),
)])

Chain(['api', 'v1', 'users', '123']).match(rule)              # True
Chain(['api', 'v1', 'admin', 'dashboard']).match(rule)        # True
Chain(['api', 'v1', 'admin', 'secret']).match(rule)            # False
Chain(['api', 'v2', 'users', '123']).match(rule)               # False
```

### Log filtering

```python
from latychain import Chain, ChainRuleAtom

rule = Chain([
    ChainRuleAtom.rex(r'\d{4}'),
    ChainRuleAtom.rex(r'\d{2}'),
    ChainRuleAtom.rex(r'\d{2}'),
    ChainRuleAtom.enum(Chain(['ERROR']), Chain(['CRITICAL'])),
    ChainRuleAtom.any(0),
])

Chain(['2024', '01', '15', 'ERROR', 'timeout']).match(rule)      # True
Chain(['2024', '01', '15', 'INFO', 'request']).match(rule)        # False
Chain(['2024', '01', '15', 'CRITICAL', 'oom']).match(rule)        # True
```

### Optional features (ext)

```python
from latychain import Chain, ChainRuleAtom

rule = Chain(['item', ChainRuleAtom.rex(r'\d+'), ChainRuleAtom.ext(Chain(['details']))])

Chain(['item', '42']).match(rule)               # True (ext skipped)
Chain(['item', '42', 'details']).match(rule)    # True (ext matched)
Chain(['item', '42', 'extra']).match(rule)      # False
```

### Custom validation (apply)

```python
from latychain import Chain, ChainRuleAtom

rule = Chain(['user', ChainRuleAtom.rex(r'[a-z]+'), ChainRuleAtom.apply(
    lambda seg: int(str(seg).lstrip('.')) > 0
)])

Chain(['user', 'alice', '42']).match(rule)    # True
Chain(['user', 'alice', '0']).match(rule)      # False
Chain(['user', 'alice', '-1']).match(rule)     # False
```

---

## Using Chains as Dict Keys

```python
from latychain import Chain

perms = {
    Chain(['admin', 'read']): True,
    Chain(['admin', 'write']): True,
    Chain(['user', 'read']): True,
    Chain(['user', 'write']): False,
}

perms[Chain(['admin', 'write'])]   # True
perms[Chain(['user', 'write'])]    # False
```

---

## `any` vs `ext`

| Feature | `any(min, max)` | `ext(chain)` |
|---------|----------------|--------------|
| What it matches | Any elements | A specific chain or nothing |
| Use case | Skip unknown content | Optional known structure |

```python
# any(0).b — any prefix works
Chain(['a', 'b']).match(Chain([ChainRuleAtom.any(0), 'b']))       # True
Chain(['x', 'y', 'b']).match(Chain([ChainRuleAtom.any(0), 'b']))  # True
Chain(['b']).match(Chain([ChainRuleAtom.any(0), 'b']))            # True

# .a.ext(.a).b — only .a.b or .a.a.b
pat = Chain(['a', ChainRuleAtom.ext(Chain(['a'])), 'b'])
Chain(['a', 'b']).match(pat)       # True
Chain(['a', 'a', 'b']).match(pat)  # True
Chain(['a', 'x', 'b']).match(pat)  # False
```
