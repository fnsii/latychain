# useLatyChain
"""Verify all sugar-syntax code snippets from the README."""
from latychain import Chain, ChainPatternAtom, Patom

# ── data chain ──
data = .heading.h1
assert data == Chain(['heading', 'h1']), f"data: {data}"

# ── rule chain ──
rule = .any(0).uuu.rex(r'x\d')
assert rule == Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])

# ── matching: THIS WAS BROKEN in README ──
# .x.uuu.x1.match(rule)  -- CANNOT WORK, .match() gets absorbed into chain expression
# Fix: assign to variable first, then call .match()
x = .x.uuu.x1
assert x == Chain(['x', 'uuu', 'x1'])
assert x.match(rule) == True

# ── nested enum ──
rule2 = .any(0).enum(
    .admin.any(0),
    .user.any(0),
).rex(r'\d+')
assert Chain(['user', 'login', '123']).match(rule2) == True

# ── runner.py (entry point) ──
import latychain.ChainDotRule
# Just verify it's registered
import sys
found = any('LatyFinder' in str(type(f)) for f in sys.meta_path)
assert found, "Import hook not registered"

print("✅ All README sugar snippets verified!")
