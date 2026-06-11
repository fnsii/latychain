# latychain

**Chain-structured data and pattern matching with `.xxx.yyy` syntax.**

`latychain` provides two core types — [`Chain`](#chain) (immutable ordered container) and [`ChainRuleAtom`](#chainruleatom) (rule atoms) — plus an optional **import hook** that enables the concise `.xxx.yyy` syntax for constructing chains.

```python
import latychain.ChainDotRule   # enable .xxx.yyy sugar
from latychain import Chain

# ── Data chain ──
heading = .heading.h1                    # → Chain(['heading', 'h1'])

# ── Rule chain ──
rule = .any(0).uuu.rex(r'x\d')           # → Chain([any(0), 'uuu', rex(...)])

# ── Nested rules ──
r2 = .any(0).enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(f)
)

# ── Matching ──
.x.uuu.x1.match(rule)                    # True
```

---

## Table of Contents

- [Why latychain?](#why-latychain)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Chain](#chain)
  - [Construction](#construction)
  - [Operations](#operations)
  - [Methods](#methods)
- [ChainRuleAtom](#chainruleatom)
  - [any — arbitrary elements](#any--arbitrary-elements)
  - [rex — regex match](#rex--regex-match)
  - [enum — choice](#enum--choice)
  - [apply — custom predicate](#apply--custom-predicate)
  - [long — string length](#long--string-length)
  - [un — negation](#un--negation)
  - [ext — optional segment](#ext--optional-segment)
- [Matching](#matching)
  - [Full match vs partial match](#full-match-vs-partial-match)
  - [Backtracking engine](#backtracking-engine)
- [`.xxx.yyy` Syntax Sugar](#xxxyyy-syntax-sugar)
  - [How it works](#how-it-works)
  - [What is (and isn't) transformed](#what-is-and-isnt-transformed)
  - [Nested expressions](#nested-expressions)
- [Examples](#examples)
  - [HTML headings](#html-headings)
  - [Path permissions](#path-permissions)
  - [Log classification](#log-classification)
- [API Reference](#api-reference)
- [Design & Implementation](#design--implementation)
- [Development](#development)

---

## Why latychain?

Many domains deal with **hierarchical path-like data**: CSS selectors, filesystem paths, JSON paths, routing rules, config keys, log categories, etc. Representing these as plain strings is error-prone; representing them as lists is verbose.

`latychain` gives you:

- **Immutability** — chains are hashable, thread-safe, usable as dict keys
- **Pattern matching** — declarative rules with backtracking, regex, custom predicates
- **Concise syntax** — `.xxx.yyy` reads naturally as a path
- **No external dependencies** — pure Python, uses only standard library

---

## Installation

```bash
pip install latychain
```

Requires Python 3.10+.

---

## Quick Start

```python
import latychain.ChainDotRule
from latychain import Chain

# ── Construct data chains ──
path = .user.profile.avatar
# → Chain(['user', 'profile', 'avatar'])

# ── Construct rule chains ──
rule = .any(0).enum(
    .admin.any(0),
    .user.any(0)
).rex(r'\d+')

# ── Match ──
.user.login.123.match(rule)       # True
.admin.delete.456.match(rule)     # True
.guest.abc.match(rule)            # False
```

---

## Chain

`Chain` is an **immutable, ordered container**. Elements can be plain strings (data) or `ChainRuleAtom` instances (rules).

### Construction

```python
from latychain import Chain

Chain()                            # empty chain
Chain(['a'])                       # single element
Chain(['a', 'b', 'c'])             # multi-element
Chain([ChainRuleAtom.any(0)])      # with rule atoms
```

Or with the `.xxx.yyy` sugar:

```python
import latychain.ChainDotRule

.a.b.c                             # → Chain(['a', 'b', 'c'])
.any(0).uuu.rex(r'x\d')           # → Chain([any(0), 'uuu', rex(...)])
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
chain.startswith(prefix)           # prefix match (partial)
chain.match(pattern)               # full match (see Matching section)
chain.match(pattern, partial=True) # prefix match
```

---

## ChainRuleAtom

`ChainRuleAtom` is the minimal unit of a rule pattern. All atoms are immutable and hashable.

| Factory | Purpose |
|---------|---------|
| [`any(min, max)`](#any--arbitrary-elements) | Match N arbitrary elements (with backtracking) |
| [`rex(pattern)`](#rex--regex-match) | Regex fullmatch on a single element |
| [`enum(*chains)`](#enum--choice) | Pick one of several alternatives |
| [`apply(func, long)`](#apply--custom-predicate) | Custom predicate on N elements |
| [`long(min, max)`](#long--string-length) | String length constraint |
| [`un(value)`](#un--negation) | Negation: not equal to value |
| [`ext(chain)`](#ext--optional-segment) | Optional segment (match or skip) |

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

### any — arbitrary elements

Match between `min` and `max` arbitrary elements. Non-greedy with backtracking.

```python
.any()        # at least 1
.any(0)       # 0 or more
.any(2)       # at least 2
.any(1, 3)    # 1 to 3
.any(0, 5)    # 0 to 5
```

### rex — regex match

Regex `fullmatch` on a **single** string element.

```python
.rex(r'h[12]')     # matches 'h1', 'h2'
.rex(r'\d+')       # matches '123', '0'
```

### enum — choice

Match **one** of several alternatives. Each alternative is a `Chain` (data or rule).

```python
.enum(
    .type.h1,
    .type.h2
)
# matches .type.h1  or  .type.h2
```

### apply — custom predicate

Apply a user function to `long` consecutive elements. The function receives a `Chain` object.

```python
.apply(lambda seg: str(seg).startswith('.x'))
# single element starting with 'x'

.apply(lambda seg: len(seg) > 2, long=2)
# two consecutive elements, total chain length > 2
```

### long — string length

Constrain the **string length** of a single element.

```python
.long(3)          # exactly 3 characters
.long(2, 5)       # 2 to 5 characters
```

### un — negation

Match any single element **except** the given value.

```python
.un('admin')      # matches 'user', 'guest'; does NOT match 'admin'
```

### ext — optional segment

Try to match the inner chain; if it fails, skip (consume 0 elements).

```python
.a.ext(.pi).b
# matches .a.pi.b  (ext matched)
# matches .a.b      (ext skipped)
# does NOT match .a.x.b
```

---

## Matching

### Full match vs partial match

```python
data = .a.b.c.d

data.match(.a.b)              # False — does not consume c.d
data.match(.a.b, partial=True) # True  — prefix matches
```

### Backtracking engine

The matcher uses **depth-first backtracking with non-greedy priority**. `any()` tries shorter matches first, then longer ones if the rest of the pattern fails.

```
Rule: .any(0).uuu.rex(r'x\d')
Data: .pre.uuu.x1

Attempts:
  any=0 → uuu ≠ 'pre' → backtrack
  any=1 → uuu = 'uuu' ✓ → rex(r'x\d') matches 'x1' ✓ → success
```

---

## `.xxx.yyy` Syntax Sugar

### Enabling

```python
import latychain.ChainDotRule
```

This registers a **meta path finder** (import hook) that transforms all subsequently loaded `.py` files. Only needs to be done once, at the entry point.

### How it works

The import hook uses Python's `tokenize` module to safely identify `.xxx` expressions and transform them into `Chain([...])` calls at compile time (not runtime).

| Source | Transformed to |
|--------|---------------|
| `.heading.h1` | `Chain(['heading', 'h1'])` |
| `.any(0).uuu` | `Chain([ChainRuleAtom.any(0), 'uuu'])` |
| `.any(0).uuu.rex(r'x\d')` | `Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])` |

**Rule**: segments without `()` become strings; segments with `()` become `ChainRuleAtom.xxx()` calls.

### What is (and isn't) transformed

| Code | Transformed? | Reason |
|------|-------------|--------|
| `.heading.h1` | ✅ Yes | chain expression |
| `.any(0).uuu` | ✅ Yes | chain expression |
| `obj.attr` | ❌ No | attribute access |
| `.5 + .3` | ❌ No | float literals |
| `func().attr` | ❌ No | method return value access |
| `"strings .here"` | ❌ No | inside string literals |
| `# comments .here` | ❌ No | inside comments |

### Nested expressions

Arguments inside `enum()`, `ext()`, etc. are recursively transformed:

```python
.enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(f)
)
# → Chain([ChainRuleAtom.enum(
#     Chain(['hi', ChainRuleAtom.rex(r'x[0-9]')]),
#     Chain(['wuhu', ChainRuleAtom.apply(f)])
# )])
```

---

## Examples

### HTML headings

```python
import latychain.ChainDotRule

heading_rule = .any(0).heading.rex(r'h[1-6]')

.heading.h1.match(heading_rule)          # True
.body.heading.h3.match(heading_rule)     # True
.heading.h7.match(heading_rule)          # False
```

### Path permissions

```python
import latychain.ChainDotRule

# Allow /user/* and /admin/*, but reject /admin/secret
allow_rule = .any(0).enum(
    .user.any(0),
    .admin.un('secret').any(0)
)

.a.user.profile.match(allow_rule)        # True
.a.admin.dashboard.match(allow_rule)      # True
.a.admin.secret.match(allow_rule)          # False
```

### Log classification

```python
import latychain.ChainDotRule

# Match error logs: YYYY.MM.DD.ERROR.xxx
error_pattern = (
    .rex(r'\d{4}')
    .rex(r'\d{2}')
    .rex(r'\d{2}')
    .ERROR
    .any(0)
)

.2024.01.15.ERROR.timeout.match(error_pattern)     # True
.2024.01.15.INFO.request.match(error_pattern)       # False
```

---

## API Reference

### `Chain`

```python
class Chain:
    def __init__(self, elements: Iterable = ()) -> None

    # Read
    def __getitem__(self, index: int) -> str | ChainRuleAtom
    def __len__(self) -> int
    def __iter__(self) -> Iterator
    @property
    def elements(self) -> tuple

    # String
    def __str__(self) -> str       # ".a.b.c"
    def __repr__(self) -> str      # "Chain(['a', 'b', 'c'])"

    # Value semantics
    def __eq__(self, other) -> bool
    def __hash__(self) -> int
    def __bool__(self) -> bool

    # Operations
    def __add__(self, other) -> Chain
    def match(self, pattern: Chain, partial: bool = False) -> bool

    # Utilities
    def to_list(self) -> list
    def startswith(self, prefix: Chain) -> bool
```

### `ChainRuleAtom`

```python
class ChainRuleAtom:
    @staticmethod
    def any(min: int = 0, max: int = 0) -> ChainRuleAtom
    @staticmethod
    def rex(pattern: str) -> ChainRuleAtom
    @staticmethod
    def enum(*alternatives: Chain) -> ChainRuleAtom
    @staticmethod
    def apply(func: callable, long: int = 1) -> ChainRuleAtom
    @staticmethod
    def long(min: int, max: int | None = None) -> ChainRuleAtom
    @staticmethod
    def un(value: str) -> ChainRuleAtom
    @staticmethod
    def ext(chain: Chain | None = None) -> ChainRuleAtom
```

### `latychain.ChainDotRule`

```python
import latychain.ChainDotRule   # registers the import hook globally
```

---

## Design & Implementation

Detailed documentation is in the [`docs/`](./docs/) directory:

| Document | Description |
|----------|-------------|
| [`docs/api-reference.md`](./docs/api-reference.md) | Complete API reference for Chain, ChainRuleAtom, and the import hook |
| [`docs/guide.md`](./docs/guide.md) | Usage guide with practical patterns, migration tips, and deep dives |

### Key design decisions

1. **Single type for data and rules** — `Chain` holds both strings and `ChainRuleAtom` instances, no separate DSL
2. **Compile-time transformation** — import hook uses `tokenize`, not runtime evaluation; safe and performant
3. **Backtracking engine** — non-greedy depth-first search for `any()` matching
4. **Immutability** — chains are hashable, thread-safe, usable as dict keys

---

## Development

### Setup

```bash
git clone <repo>
cd latychain
uv venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
```

### Running tests

```bash
uv run python test/run_all.py
```

### Project structure

```
latychain/
├── src/latychain/
│   ├── __init__.py          # Public API: Chain, ChainRuleAtom
│   ├── _chain.py            # Chain class + backtracking matcher
│   ├── _atoms.py            # ChainRuleAtom + 7 rule atom types
│   ├── _hook.py             # Import hook (tokenize transformer)
│   └── ChainDotRule.py      # Entry point: import to enable sugar
├── test/
│   ├── run_all.py           # Test runner
│   ├── test_core.py         # Core API tests (30 cases)
│   └── _test_sugar.py       # Sugar syntax integration tests
├── docs/
│   ├── api-reference.md     # Complete API reference
│   └── guide.md             # Usage guide and practical patterns
├── pyproject.toml           # Project metadata
└── README.md                # This file
```
