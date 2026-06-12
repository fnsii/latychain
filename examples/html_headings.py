"""
Example 1 — HTML heading detection
===================================

Parse a flat token stream (e.g. from an HTML tokenizer) and detect heading
elements ``h1`` through ``h6``.  Invalid levels like ``h7`` or ``h0`` are
rejected.

Run:  python examples/html_headings.py
"""

from latychain import Chain, Patom

# ── Pattern ─────────────────────────────────────────────────
#  Chain / Patom.any(0)       → skip unknown tokens before the heading
#           / "heading"       → literal 'heading' token
#           / Patom.rex(...)  → exactly h1 through h6
# ────────────────────────────────────────────────────────────

heading_rule = (
    Chain
    / Patom.any(0)
    / "heading"
    / Patom.rex(r"h[1-6]")
)

# ── Test cases ──────────────────────────────────────────────

tests = [
    (["heading", "h1"],         True,   "basic h1"),
    (["body", "heading", "h3"], True,   "h3 after body"),
    (["div", "p", "heading", "h6", "text"], True, "h6 with trailing content (partial match)"),
    (["heading", "h7"],         False,  "h7 out of range"),
    (["heading", "h0"],         False,  "h0 out of range"),
    (["h1"],                    False,  "missing 'heading' token"),
    (["heading"],               False,  "missing level"),
    ([],                        False,  "empty"),
]

print("=" * 55)
print("HTML heading detection")
print("=" * 55)

for tokens, expected, label in tests:
    data = Chain(tokens)
    result = data.match(heading_rule, partial=True)  # partial — only prefix needs to match
    status = "✓" if result == expected else "✗ FAIL"
    print(f"  {status}  {label:40s}  → {result}")
