# Examples

Six small, self-contained projects showing what **latychain** can do.

Each script is runnable — just `python examples/<name>.py` from the repo root
(or `uv run python examples/<name>.py`).

| Example | What it demonstrates |
|---------|---------------------|
| [`html_headings.py`](html_headings.py) | Detect HTML heading tags (`h1`–`h6`) anywhere in a token stream; reject invalid levels |
| [`api_routing.py`](api_routing.py) | Match API paths, enforce role-based permissions (admin vs user), block secret routes |
| [`log_classifier.py`](log_classifier.py) | Classify log lines by date format + severity; filter ERROR / CRITICAL at scale |
| [`config_validator.py`](config_validator.py) | Validate deep configuration paths with optional segments and custom value checks |
| [`mini_commands.py`](mini_commands.py) | Build a tiny command DSL with subcommands, flags, and positional arguments — all via pattern matching |
| [`perm_tables.py`](perm_tables.py) | Use immutable Chains as hashable dict keys for role → permission lookup tables |

All examples use two construction styles — the standard `Chain([...])` form, and the
optional `/` + `Patom` shortcut:

```python
from latychain import Chain, ChainPatternAtom as Patom

# Standard explicit
rule = Chain([Patom.any(0), "user", Patom.any(0)])

# / shortcut
rule = Chain / Patom.any(0) / "user" / Patom.any(0)

data = Chain / "a" / "user" / "login"
data.match(rule)   # True
```
