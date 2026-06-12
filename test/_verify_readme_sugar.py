# useLatyChain
"""Verify all sugar-syntax code snippets from the README."""
from latychain import Chain, ChainPatternAtom, Patom

# ── data chain ──
data = .heading.h1
assert data == Chain(['heading', 'h1']), f"data: {data}"

# ── rule chain ──
rule = .any(0).uuu.rex(r'x\d')
assert rule == Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])

# ── matching: pattern.match(data) ──
x = .x.uuu.x1
assert x == Chain(['x', 'uuu', 'x1'])
assert rule.match(x) == True

# ── nested enum ──
rule2 = .any(0).enum(
    .admin.any(0),
    .user.any(0),
).rex(r'\d+')
assert rule2.match(Chain(['user', 'login', '123'])) == True

# ── runner.py (entry point) ──
import latychain.ChainDotRule
# Just verify it's registered
import sys
found = any('LatyFinder' in str(type(f)) for f in sys.meta_path)
assert found, "Import hook not registered"

print("✅ All README sugar snippets verified!")
