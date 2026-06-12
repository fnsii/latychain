"""
Example 4 — Configuration path validator
=========================================

Validate deep configuration paths against a schema.  Demonstrates:

* ``ext`` — optional segments (``.details`` may or may not be present)
* ``any(0)`` — absorb unknown sub-keys
* ``apply`` — custom validation on a config value

Run:  python examples/config_validator.py
"""

from latychain import Chain, Patom

# ── Schema ──────────────────────────────────────────────────
#   config.database.connection.pool.ext(.details).any(0)
# ────────────────────────────────────────────────────────────

schema = (
    Chain
    / "config"
    / "database"
    / "connection"
    / "pool"
    / Patom.ext(Chain(["details"]))  # optional "details" segment
    / Patom.any(0)                  # remaining keys
)

# ── Value validator ─────────────────────────────────────────
#  user.<name>.apply(...) — custom check on the value
# ────────────────────────────────────────────────────────────

value_rule = (
    Chain
    / "user"
    / Patom.rex(r"[a-z]+")  # lowercase name
    / Patom.apply(
        lambda seg: int(str(seg).lstrip(".")) > 0
    )  # positive integer id
)

# ── Test cases ──────────────────────────────────────────────

print("=" * 55)
print("Config path validation")
print("=" * 55)

configs = [
    (["config", "database", "connection", "pool", "5"],        True),
    (["config", "database", "connection", "pool"],             True),
    (["config", "database", "connection", "pool", "details"],  True),
    (["config", "database", "connection", "pool", "details", "max"], True),
    (["config", "database", "timeout"],                        False),
    (["config", "database"],                                   False),
    (["config"],                                               False),
]

for tokens, expected in configs:
    data = Chain(tokens)
    result = data.match(schema)
    status = "✓" if result == expected else "✗ FAIL"
    path = ".".join(tokens)
    print(f"  {status}  {path:55s}  → {result}")

print()
print("=" * 55)
print("Value validation  (user.<name>.<positive-id>)")
print("=" * 55)

values = [
    (["user", "alice", "42"],   True,  "alice id=42"),
    (["user", "bob", "7"],      True,  "bob id=7"),
    (["user", "alice", "0"],    False, "id=0 rejected"),
    (["user", "alice", "-1"],   False, "id=-1 rejected"),
    (["user", "ALICE", "42"],   False, "uppercase name rejected"),
    (["user", "a", "42"],        True,  "single-char name"),
]

for tokens, expected, label in values:
    data = Chain(tokens)
    result = data.match(value_rule)
    status = "✓" if result == expected else "✗ FAIL"
    print(f"  {status}  {label:25s}  → {result}")
