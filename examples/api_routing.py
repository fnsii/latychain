"""
Example 2 — API routing & permissions
======================================

Match REST-style API paths and enforce role-based access:

* ``api/v1/users/<id>``    — anyone can access
* ``api/v1/admin/<action>`` — admin allowed, *except* secret actions
* ``api/v2/...``            — rejected (version mismatch)

The ``un`` atom blocks a forbidden segment; ``any(0)`` absorbs trailing
path components.

Run:  python examples/api_routing.py
"""

from latychain import Chain, Patom

# ── Pattern ─────────────────────────────────────────────────
#   api.v1.enum(
#       .users.any(0),                         # user routes — open
#       .admin.un('secret').any(0)             # admin routes — block 'secret'
#   )
# ────────────────────────────────────────────────────────────

route_rule = (
    Chain
    / "api"
    / "v1"
    / Patom.enum(
        Chain / "users" / Patom.any(0),
        Chain / "admin" / Patom.un("secret") / Patom.any(0),
    )
)

# ── Test cases ──────────────────────────────────────────────

tests = [
    (["api", "v1", "users", "123"],            True,  "user profile"),
    (["api", "v1", "users"],                   True,  "user list"),
    (["api", "v1", "admin", "dashboard"],      True,  "admin dashboard"),
    (["api", "v1", "admin", "delete", "123"],  True,  "admin delete (allowed)"),
    (["api", "v1", "admin", "secret"],         False, "admin secret (BLOCKED)"),
    (["api", "v1", "admin", "secret", "x"],    False, "admin secret + args (BLOCKED)"),
    (["api", "v2", "users", "123"],            False, "v2 rejected"),
    (["api", "v1", "guest"],                   False, "unknown role"),
]

print("=" * 55)
print("API routing & permissions")
print("=" * 55)

for tokens, expected, label in tests:
    data = Chain(tokens)
    result = data.match(route_rule)
    status = "✓" if result == expected else "✗ FAIL"
    print(f"  {status}  {label:40s}  → {result}")
