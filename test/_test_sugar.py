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

# ---- Match: pattern.match(data) ----
r = .any(0).uuu.rex(r'x\d')
data = Chain / "x" / "uuu" / "x1"
assert r.match(data), "basic regex match"
assert not r.match(Chain / "x" / "yyy" / "x1"), "regex no-match"

# any with min=1
r_any1 = .any(1).end
assert r_any1.match(Chain / "a" / "end")
assert not r_any1.match(Chain / "end")

# any with min=0
r_any0 = .any(0).end
assert r_any0.match(Chain / "end")
assert r_any0.match(Chain / "a" / "end")

# Ext: optional segment
er = .a.ext(.pi).b
assert er.match(Chain / "a" / "b"), "ext skip"
assert er.match(Chain / "a" / "pi" / "b"), "ext match"
assert not er.match(Chain / "a" / "x" / "b"), "ext partial fail"

# Nested enum
r2 = .any(0).enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(lambda c: str(c).startswith('.x'))
)
assert r2.match(Chain / "pre" / "hi" / "x5"), "enum first alt"
assert r2.match(Chain / "pre" / "wuhu" / "xok"), "enum second alt"
assert not r2.match(Chain / "pre" / "hi" / "abc"), "enum no-match"

# Un: negation
r_un = .un('admin')
assert r_un.match(Chain / "user"), "un match"
assert not r_un.match(Chain / "admin"), "un no-match"
# Un with quoted comma
r_un_comma = .un('a,b')
assert not r_un_comma.match(Chain / "a,b"), "un: a,b equals a,b should not match"
assert r_un_comma.match(Chain / "x"), "un: x != a,b should match"

# Len: string length constraint
r_len = .len(2, 4)
assert r_len.match(Chain / "abc"), "len match"
assert not r_len.match(Chain / "a"), "len no-match"
assert not r_len.match(Chain / "abcde"), "len too long"

# Apply: custom function
r_apply = .apply(lambda c: len(c) == 1)
assert r_apply.match(Chain / "abc"), "apply single"
assert not r_apply.match(Chain / "a" / "b"), "apply no-match"

# Apply with count=2
r_apply2 = .apply(lambda c: len(c) == 2, 2)
assert r_apply2.match(Chain / "a" / "b"), "apply count=2 match"
assert not r_apply2.match(Chain / "a"), "apply count=2 too short"

# ---- Partial match (use explicit Chain, not sugar .match()) ----
data = Chain / "a" / "b" / "c" / "d"
assert Chain(["a", "b"]).match(data, partial=True), "partial yes"
assert not Chain(["a", "b"]).match(data, partial=False), "partial no"

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

# ---- Chain / Chain ----
assert (Chain / "a" / "b") / (Chain / "c" / "d") == Chain(["a", "b", "c", "d"])

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
assert r_paren.match(Chain / "a(b)c"), "regex with literal parens"
assert not r_paren.match(Chain / "abc"), "literal parens not in data"

# ---- ext() with invalid argument (should raise TypeError) ----
no_err = True
try:
    ChainPatternAtom.ext(123)  # int is not valid
    no_err = False
except TypeError:
    pass
assert no_err, "ext() should reject non-Chain/str/atom argument"

# ---- ext() with no argument should raise TypeError ----
no_err = True
try:
    ChainPatternAtom.ext()
    no_err = False
except TypeError:
    pass
assert no_err, "ext() should require an argument"

# ---- unregister test ----
import latychain.ChainDotRule
latychain.ChainDotRule.unregister()
latychain.ChainDotRule.register()

# ---- Patom is ChainPatternAtom ----
assert Patom is ChainPatternAtom
assert Patom.any() == ChainPatternAtom.any()

print("✅ All sugar tests passed!")
