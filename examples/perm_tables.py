"""
Example 6 — Permission lookup tables
======================================

Because Chains are **immutable and hashable**, they can be used as
dictionary keys.  This example builds a role→permission table where
each key is a ``Chain([role, action])``.

Bonus: ``any(0)`` lets us write wildcard rules that match *any* action
for a given role.

Run:  python examples/perm_tables.py
"""

from latychain import Chain, Patom

# ── Permission table (Chain keys) ───────────────────────────

perms = {
    Chain / "admin" / "read":    True,
    Chain / "admin" / "write":   True,
    Chain / "admin" / "delete":  True,
    Chain / "admin" / "config":  True,
    Chain / "user" / "read":     True,
    Chain / "user" / "write":    False,
    Chain / "user" / "delete":   False,
    Chain / "user" / "config":   False,
    Chain / "guest" / "read":    True,
    Chain / "guest" / "write":   False,
    Chain / "guest" / "delete":  False,
    Chain / "guest" / "config":  False,
}

# ── Wildcard matching with any(0) ───────────────────────────
# "admin.any(0)" matches any admin action — no need to list them all.
admin_wildcard = Chain / "admin" / Patom.any(0)


def can(role: str, action: str) -> bool:
    """Check explicit permission; fall back to wildcard check."""
    key = Chain / role / action
    if key in perms:
        return perms[key]
    return key.match(admin_wildcard)


# ── Test ────────────────────────────────────────────────────

print("=" * 55)
print("Permission lookup tables")
print("=" * 55)

tests = [
    ("admin", "read"),
    ("admin", "write"),
    ("admin", "delete"),
    ("admin", "config"),
    ("admin", "sudo"),       # not in table, but wildcard should match
    ("user", "read"),
    ("user", "write"),
    ("user", "delete"),
    ("guest", "read"),
    ("guest", "write"),
    ("guest", "unknown"),    # not in table, wildcard only for admin
]

print(f"  {'role':8s} {'action':10s} {'allowed':8s}  source")
print(f"  {'-'*8} {'-'*10} {'-'*8}  {'-'*20}")

for role, action in tests:
    key = Chain / role / action
    allowed = can(role, action)
    if key in perms:
        source = "explicit table"
    elif key.match(admin_wildcard):
        source = "admin wildcard"
    else:
        source = "denied (no match)"
    print(f"  {role:8s} {action:10s} {str(allowed):8s}  {source}")
