# latychain

> **⚠️ Early Development** — API may change.

**Chain-structured data and pattern matching.**

`latychain` provides two core types — [`Chain`](#chain) (immutable ordered container) and [`ChainRuleAtom`](#chainruleatom) (rule atoms). An optional **import hook** enables the concise `.xxx.yyy` syntax in separate module files.

```python
from latychain import Chain, ChainRuleAtom

# ── Data chain ──
heading = Chain(['heading', 'h1'])

# ── Rule chain ──
rule = Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])

# ── Matching ──
data = Chain(['x', 'uuu', 'x1'])
data.match(rule)                         # True
```

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Chain](#chain)
- [ChainRuleAtom](#chainruleatom)
- [Matching](#matching)
- [`.xxx.yyy` Syntax Sugar](#xxxyyy-syntax-sugar)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Development](#development)

---

## Installation

```bash
pip install latychain
```

Requires Python 3.10+.

---

## Quick Start

```python
from latychain import Chain, ChainRuleAtom

# ── Data chains ──
path = Chain(['user', 'profile', 'avatar'])
heading = Chain(['heading', 'h1'])

# ── Rule chains ──
rule = Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])

rule2 = Chain([
    ChainRuleAtom.any(0),
    ChainRuleAtom.enum(
        Chain(['admin', ChainRuleAtom.any(0)]),
        Chain(['user', ChainRuleAtom.any(0)]),
    ),
    ChainRuleAtom.rex(r'\d+'),
])

# ── Matching ──
Chain(['x', 'uuu', 'x1']).match(rule)               # True
Chain(['user', 'login', '123']).match(rule2)         # True
Chain(['admin', 'delete', '456']).match(rule2)       # True
Chain(['guest', 'abc']).match(rule2)                 # False
```

All code above works in a single `.py` file with no special setup.

---

## Chain

`Chain` is an **immutable, ordered container**. Elements can be plain strings (data) or `ChainRuleAtom` instances (rules).

### Construction

```python
from latychain import Chain

Chain()                            # empty chain
Chain(['a'])                       # single element
Chain(['a', 'b', 'c'])             # multi-element
```

### Operations

```python
c = Chain(['a', 'b', 'c'])

len(c)                             # 3
c[0]                               # 'a'
c[-1]                              # 'c'
list(c)                            # ['a', 'b', 'c']
c.elements                         # ('a', 'b', 'c')

str(c)                             # ".a.b.c"
repr(c)                            # "Chain(['a', 'b', 'c'])"

Chain(['a', 'b']) == Chain(['a', 'b'])     # True
Chain(['a', 'b']) + Chain(['c', 'd'])      # → Chain(['a','b','c','d'])

d = {Chain(['a']): 1}              # hashable, usable as dict key
```

### Methods

```python
chain.to_list()                    # → list of elements
chain.startswith(prefix)           # prefix match
chain.match(pattern)               # full match
chain.match(pattern, partial=True) # prefix match
```

---

## ChainRuleAtom

`ChainRuleAtom` is the minimal unit of a pattern rule. All atoms are immutable and hashable.

| Factory | Purpose |
|---------|---------|
| `any(min, max)` | Match N arbitrary elements (with backtracking) |
| `rex(pattern)` | Regex fullmatch on a single element |
| `enum(*chains)` | Pick one of several alternatives |
| `apply(func, long)` | Custom predicate on N elements |
| `long(min, max)` | String length constraint |
| `un(value)` | Negation: not equal to value |
| `ext(chain)` | Optional segment (match or skip) |

```python
from latychain import ChainRuleAtom

ChainRuleAtom.any(0)
ChainRuleAtom.rex(r'x\d')
ChainRuleAtom.enum(Chain(['a']), Chain(['b']))
ChainRuleAtom.apply(lambda c: len(c) > 2)
ChainRuleAtom.long(3, 5)
ChainRuleAtom.un('admin')
ChainRuleAtom.ext(Chain(['a', 'b']))
```

### `any(min=0, max=0)` — arbitrary elements

| Example | Meaning |
|---------|---------|
| `any()` | At least 1 element |
| `any(0)` | 0 or more |
| `any(2)` | At least 2 |
| `any(1, 3)` | 1 to 3 |
| `any(0, 5)` | 0 to 5 |

Non-greedy with backtracking: tries shorter matches first.

### `rex(pattern)` — regex match

```python
Chain([ChainRuleAtom.rex(r'h[12]')]).match(Chain(['h1']))    # True
Chain([ChainRuleAtom.rex(r'\d+')]).match(Chain(['123']))     # True
```

Regex `fullmatch` on a **single** string element.

### `enum(*chains)` — choice

```python
pat = Chain([ChainRuleAtom.enum(
    Chain(['type', 'h1']),
    Chain(['type', 'h2']),
)])
Chain(['type', 'h1']).match(pat)    # True
Chain(['type', 'h3']).match(pat)    # False
```

### `apply(func, long=1)` — custom predicate

```python
# Check a single element
Chain([ChainRuleAtom.apply(
    lambda seg: str(seg).startswith('.x')
)]).match(Chain(['xhello']))     # True

# Check multiple elements (long=2)
Chain([ChainRuleAtom.apply(
    lambda seg: seg[0] != seg[1], long=2
)]).match(Chain(['a', 'b']))      # True
```

### `long(min, max=None)` — string length

```python
Chain([ChainRuleAtom.long(3)]).match(Chain(['abc']))      # True
Chain([ChainRuleAtom.long(2, 5)]).match(Chain(['abc']))   # True
```

### `un(value)` — negation

```python
Chain([ChainRuleAtom.un('admin')]).match(Chain(['user']))    # True
Chain([ChainRuleAtom.un('admin')]).match(Chain(['admin']))   # False
```

### `ext(chain=None)` — optional segment

```python
pat = Chain(['a', ChainRuleAtom.ext(Chain(['pi'])), 'b'])
Chain(['a', 'b']).match(pat)        # True (ext skipped)
Chain(['a', 'pi', 'b']).match(pat)  # True (ext matched)
Chain(['a', 'x', 'b']).match(pat)   # False
```

---

## Matching

### Backtracking engine

The matcher uses **depth-first backtracking with non-greedy priority**. `any()` tries shorter matches first, then longer ones if the rest of the pattern fails.

```
Pattern: any(0) → "uuu" → rex(r'x\d')
Data:    "pre"  → "uuu" → "x1"

Attempts:
  any=0 → "uuu" ≠ 'pre' → backtrack
  any=1 → "pre"=any, "uuu"="uuu" ✓, rex(r'x\d') matches "x1" ✓ → success
```

### Full vs partial match

```python
data = Chain(['a', 'b', 'c', 'd'])

data.match(Chain(['a', 'b']))                # False
data.match(Chain(['a', 'b']), partial=True)  # True
```

---

## `.xxx.yyy` Syntax Sugar

The import hook transforms `.xxx.yyy.zzz()` expressions into `Chain([...])` calls.

```python
.any(0).uuu.rex(r'x\d')
# → Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])
```

**Rule**: segments without `()` become strings; segments with `()` become `ChainRuleAtom.xxx()`.

> **⚠️ Important**: The import hook only transforms **imported modules**, not the entry script itself. You need **two files**:

**main.py** (runner — no sugar syntax):
```python
import latychain.ChainDotRule
import my_code      # this file gets transformed
```

**my_code.py** (uses `.xxx.yyy` sugar):
```python
from latychain import Chain

# Data chain
heading = .heading.h1               # → Chain(['heading', 'h1'])

# Rule chain
rule = .any(0).uuu.rex(r'x\d')

# Matching (call .match() on a Chain variable)
data = .x.uuu.x1
data.match(rule)                     # True
```

### What is (and isn't) transformed

| Code | Transformed? | Reason |
|------|-------------|--------|
| `.heading.h1` | ✅ Yes | chain expression |
| `.any(0).uuu` | ✅ Yes | chain expression |
| `obj.attr` | ❌ No | attribute access |
| `.5 + .3` | ❌ No | float literals |
| `func().attr` | ❌ No | method return value |
| `"strings .here"` | ❌ No | inside strings |
| `# comments .here` | ❌ No | inside comments |

### Limitations

- **Numeric-only segments (`.123`, `.42`) are not supported.** Use `Chain(['123'])` instead.
- **`.match()` is a Chain method**, not a RuleAtom. Call it on a separate Chain variable, not inside a chain expression:

```python
# ✅ Correct
data = .user.login.id123
data.match(rule)

# ❌ Wrong — .match(...) becomes ChainRuleAtom.match(...) which doesn't exist
# .user.login.id123.match(rule)
```

---

## Examples

### HTML headings

```python
from latychain import Chain, ChainRuleAtom

rule = Chain([ChainRuleAtom.any(0), 'heading', ChainRuleAtom.rex(r'h[1-6]')])

Chain(['heading', 'h1']).match(rule)          # True
Chain(['body', 'heading', 'h3']).match(rule)  # True
Chain(['heading', 'h7']).match(rule)          # False
```

### Path permissions

```python
from latychain import Chain, ChainRuleAtom

rule = Chain([ChainRuleAtom.any(0), ChainRuleAtom.enum(
    Chain(['user', ChainRuleAtom.any(0)]),
    Chain(['admin', ChainRuleAtom.un('secret'), ChainRuleAtom.any(0)]),
)])

Chain(['a', 'user', 'profile']).match(rule)         # True
Chain(['a', 'admin', 'dashboard']).match(rule)       # True
Chain(['a', 'admin', 'secret']).match(rule)           # False
```

### Log classification

```python
from latychain import Chain, ChainRuleAtom

rule = Chain([
    ChainRuleAtom.rex(r'\d{4}'),
    ChainRuleAtom.rex(r'\d{2}'),
    ChainRuleAtom.rex(r'\d{2}'),
    'ERROR',
    ChainRuleAtom.any(0),
])

Chain(['2024', '01', '15', 'ERROR', 'timeout']).match(rule)   # True
Chain(['2024', '01', '15', 'INFO', 'request']).match(rule)     # False
```

---

## API Reference

### `Chain`

```python
class Chain:
    def __init__(self, elements=()) -> None
    def __getitem__(self, index) -> str | ChainRuleAtom
    def __len__(self) -> int
    def __iter__(self) -> Iterator
    @property
    def elements(self) -> tuple
    def __str__(self) -> str       # ".a.b.c"
    def __repr__(self) -> str      # "Chain(['a', 'b', 'c'])"
    def __eq__(self, other) -> bool
    def __hash__(self) -> int
    def __bool__(self) -> bool
    def __add__(self, other) -> Chain
    def match(self, pattern, partial=False) -> bool
    def to_list(self) -> list
    def startswith(self, prefix) -> bool
```

### `ChainRuleAtom`

```python
class ChainRuleAtom:
    @staticmethod
    def any(min=0, max=0) -> ChainRuleAtom
    @staticmethod
    def rex(pattern) -> ChainRuleAtom
    @staticmethod
    def enum(*alternatives) -> ChainRuleAtom
    @staticmethod
    def apply(func, long=1) -> ChainRuleAtom
    @staticmethod
    def long(min, max=None) -> ChainRuleAtom
    @staticmethod
    def un(value) -> ChainRuleAtom
    @staticmethod
    def ext(chain=None) -> ChainRuleAtom
```

### `latychain.ChainDotRule`

Import hook for `.xxx.yyy` syntax. See [syntax sugar section](#xxxyyy-syntax-sugar).

---

## Development

```bash
git clone https://github.com/fnsii/latychain
cd latychain
uv venv && source .venv/bin/activate   # or .venv\Scripts\activate
uv run python test/run_all.py
```

### Project structure

```
latychain/
├── src/latychain/
│   ├── __init__.py          # Chain, ChainRuleAtom exports
│   ├── _chain.py            # Chain class + backtracking matcher
│   ├── _atoms.py            # ChainRuleAtom + 7 rule atom types
│   ├── _hook.py             # Import hook (tokenize transformer)
│   └── ChainDotRule.py      # Entry point for hook
├── test/
│   ├── run_all.py           # Test runner (61 tests)
│   ├── test_core.py         # Core API tests
│   ├── _test_sugar.py       # Sugar syntax tests
│   ├── _test_doc_examples.py # Doc example tests
│   └── _test_doc_sugar.py   # Sugar doc example tests
├── docs/
│   ├── api-reference.md
│   └── guide.md
├── pyproject.toml
└── README.md
```
