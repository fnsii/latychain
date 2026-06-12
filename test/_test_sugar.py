# useLatyChain
"""Test module that uses .xxx syntax (loaded via import hook)."""

from latychain import Chain, ChainPatternAtom, Patom

# ---- Pure data chains ----
h = .heading.h1
assert h == Chain / "heading" / "h1", str(h)

s = .style.font.color.red
assert s == Chain / "style" / "font" / "color" / "red", str(s)

c = .a.b.c
assert c == Chain / "a" / "b" / "c", str(c)

# ---- Match: data.match(pattern) ----
r = .any(0).uuu.rex(r'x\d')
data = Chain / "x" / "uuu" / "x1"
assert data.match(r), "basic regex match"
assert not (Chain / "x" / "yyy" / "x1").match(r), "regex no-match"

# any with min=1
r_any1 = .any(1).end
assert (Chain / "a" / "end").match(r_any1)
assert not (Chain / "end").match(r_any1)

# any with min=0
r_any0 = .any(0).end
assert (Chain / "end").match(r_any0)
assert (Chain / "a" / "end").match(r_any0)

# Ext: optional segment
er = .a.ext(.pi).b
assert (Chain / "a" / "b").match(er), "ext skip"
assert (Chain / "a" / "pi" / "b").match(er), "ext match"
assert not (Chain / "a" / "x" / "b").match(er), "ext partial fail"

# Ext empty
er2 = .a.ext().b
assert (Chain / "a" / "b").match(er2), "ext() skip"

# Nested enum
r2 = .any(0).enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(lambda c: str(c).startswith('.x'))
)
assert (Chain / "pre" / "hi" / "x5").match(r2), "enum first alt"
assert (Chain / "pre" / "wuhu" / "xok").match(r2), "enum second alt"
assert not (Chain / "pre" / "hi" / "abc").match(r2), "enum no-match"

# Un: negation
assert (Chain / "user").match(.un('admin')), "un match"
assert not (Chain / "admin").match(.un('admin')), "un no-match"
# Un with quoted comma (regression: _split_args must track quotes)
assert not (Chain / "a,b").match(.un('a,b')), "un: a,b equals a,b should not match"
assert (Chain / "x").match(.un('a,b')), "un: x != a,b should match"

# Long: string length constraint
assert (Chain / "abc").match(.long(2, 4)), "long match"
assert not (Chain / "a").match(.long(2, 4)), "long no-match"
assert not (Chain / "abcde").match(.long(2, 4)), "long too long"

# Apply: custom function
assert (Chain / "abc").match(.apply(lambda c: len(c) == 1)), "apply single"
assert not (Chain / "a" / "b").match(.apply(lambda c: len(c) == 1)), "apply no-match"

# Apply with long=2
r_apply2 = .apply(lambda c: len(c) == 2, 2)
assert (Chain / "a" / "b").match(r_apply2), "apply long=2 match"
assert not (Chain / "a").match(r_apply2), "apply long=2 too short"

# ---- Partial match ----
data = .a.b.c.d
assert data.match(.a.b, partial=True), "partial yes"
assert not data.match(.a.b, partial=False), "partial no"

# ---- / operator ----
combined = Chain / "a" / "b"
assert combined == Chain(["a", "b"]), f"/: {combined}"

c_from_class = Chain / "x" / "y"
assert c_from_class == Chain(["x", "y"])

c_from_empty = Chain() / "x" / "y"
assert c_from_empty == Chain(["x", "y"])

c_rtruediv = "x" / (Chain / "y")
assert c_rtruediv == Chain(["x", "y"])

# ---- str / repr ----
assert str(.a.b.c) == ".a.b.c"
assert repr(.a.b.c) == "Chain(['a', 'b', 'c'])"

# ---- startswith ----
assert (Chain / "a" / "b" / "c").startswith(Chain / "a" / "b")
assert not (Chain / "a" / "b" / "c").startswith(Chain / "b")

# ---- Multi-line sugar syntax ----
ml = .a
    .b
    .c
assert ml == Chain / "a" / "b" / "c", f"multi-line: {ml}"

ml2 = .any(0).enum(
    .admin.any(0),
    .user.any(0)
).rex(r'\d+')
assert isinstance(ml2, Chain), f"multi-line with enum: {ml2}"

# ---- Regex with literal parens (string-aware paren matching) ----
r_paren = .rex(r'a\(b\)c')
assert (Chain / "a(b)c").match(r_paren), "regex with literal parens"
assert not (Chain / "abc").match(r_paren), "literal parens not in data"

# ---- ext() with invalid argument (should raise TypeError) ----
no_err = True
try:
    ChainPatternAtom.ext("not a chain")
    no_err = False
except TypeError:
    pass
assert no_err, "ext() should reject non-Chain argument"

# ---- unregister test ----
import latychain.ChainDotRule
latychain.ChainDotRule.unregister()
latychain.ChainDotRule.register()

# ---- Patom is ChainPatternAtom ----
assert Patom is ChainPatternAtom
assert Patom.any() == ChainPatternAtom.any()

print("✅ All sugar tests passed!")
