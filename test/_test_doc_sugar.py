# useLatyChain
"""Test doc examples that use `.xxx.yyy` sugar syntax.

Loaded via import hook (run from _run_doc_sugar.py).
"""

from latychain import Chain, ChainPatternAtom, Patom

# ═══════════════════════════════════════════════════════════
# README banner
# ═══════════════════════════════════════════════════════════
heading = .heading.h1
assert heading == Chain(['heading', 'h1'])

rule = .any(0).uuu.rex(r'x\d')
assert rule == Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])

r2 = .any(0).enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(lambda c: str(c).startswith('.x'))
)
assert r2.match(Chain(['pre', 'hi', 'x5']))
assert r2.match(Chain(['pre', 'wuhu', 'xok']))

x = .x.uuu.x1
assert x == Chain(['x', 'uuu', 'x1'])
assert rule.match(x)

# ═══════════════════════════════════════════════════════════
# Quick Start
# ═══════════════════════════════════════════════════════════
path = .user.profile.avatar
assert path == Chain(['user', 'profile', 'avatar'])

rule2 = .any(0).enum(
    .admin.any(0),
    .user.any(0)
).rex(r'\d+')

assert rule2.match(Chain(['user', 'login', '123']))
assert rule2.match(Chain(['admin', 'delete', '456']))
assert not rule2.match(Chain(['guest', 'abc']))

# ═══════════════════════════════════════════════════════════
# Chain construction (sugar)
# ═══════════════════════════════════════════════════════════
assert .a.b.c == Chain(['a', 'b', 'c'])
assert .any(0).uuu.rex(r'x\d') == Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])

# ═══════════════════════════════════════════════════════════
# any examples
# ═══════════════════════════════════════════════════════════
r_any = .any()
assert r_any.match(Chain(['x', 'y']))        # at least 1
assert not r_any.match(Chain([]))            # empty fails

r_any0 = .any(0)
assert r_any0.match(Chain(['x', 'y']))       # 0 or more
assert r_any0.match(Chain([]))               # empty ok

r_any2 = .any(2)
assert r_any2.match(Chain(['x', 'y', 'z']))  # at least 2

r_any13z = .any(1, 3).z
assert r_any13z.match(Chain(['x', 'y', 'z']))  # 1-3 then 'z'

r_any05 = .any(0, 5)
assert r_any05.match(Chain(['x', 'y']))      # 0-5

# ═══════════════════════════════════════════════════════════
# rex examples
# ═══════════════════════════════════════════════════════════
r_rex = .rex(r'h[12]')
assert r_rex.match(Chain(['h1']))
assert r_rex.match(Chain(['h2']))
assert not r_rex.match(Chain(['h3']))

r_digits = .rex(r'\d+')
assert r_digits.match(Chain(['123']))
assert r_digits.match(Chain(['0']))

# ═══════════════════════════════════════════════════════════
# enum examples
# ═══════════════════════════════════════════════════════════
enum_pat = .enum(
    .type.h1,
    .type.h2
)
assert enum_pat.match(Chain(['type', 'h1']))
assert enum_pat.match(Chain(['type', 'h2']))
assert not enum_pat.match(Chain(['type', 'h3']))

# ═══════════════════════════════════════════════════════════
# apply examples
# ═══════════════════════════════════════════════════════════
r_apply = .apply(lambda seg: str(seg).startswith('.x'))
assert r_apply.match(Chain(['xhello']))

r_apply2 = .apply(lambda seg: seg[0] != seg[1], 2)
assert r_apply2.match(Chain(['a', 'b']))

# ═══════════════════════════════════════════════════════════
# len examples
# ═══════════════════════════════════════════════════════════
r_len3 = .len(3)
assert r_len3.match(Chain(['abc']))
assert not r_len3.match(Chain(['ab']))

r_len25 = .len(2, 5)
assert r_len25.match(Chain(['abc']))

# ═══════════════════════════════════════════════════════════
# un examples
# ═══════════════════════════════════════════════════════════
r_un = .un('admin')
assert r_un.match(Chain(['user']))
assert not r_un.match(Chain(['admin']))

# ═══════════════════════════════════════════════════════════
# ext examples
# ═══════════════════════════════════════════════════════════
ext_pat = .a.ext(.pi).b
assert ext_pat.match(Chain(['a', 'b']))
assert ext_pat.match(Chain(['a', 'pi', 'b']))
assert not ext_pat.match(Chain(['a', 'x', 'b']))

# ═══════════════════════════════════════════════════════════
# Full vs partial match
# ═══════════════════════════════════════════════════════════
data = .a.b.c.d
r_ab = .a.b
assert not r_ab.match(data)
assert r_ab.match(data, partial=True)
r_any0_d = .any(0).d
assert r_any0_d.match(data)

# ═══════════════════════════════════════════════════════════
# Examples: HTML headings
# ═══════════════════════════════════════════════════════════
heading_rule = .any(0).heading.rex(r'h[1-6]')
assert heading_rule.match(Chain(['heading', 'h1']))
assert heading_rule.match(Chain(['body', 'heading', 'h3']))
assert not heading_rule.match(Chain(['heading', 'h7']))

# ═══════════════════════════════════════════════════════════
# Examples: Path permissions
# ═══════════════════════════════════════════════════════════
allow_rule = .any(0).enum(
    .user.any(0),
    .admin.un('secret').any(0)
)
assert allow_rule.match(Chain(['a', 'user', 'profile']))
assert allow_rule.match(Chain(['a', 'admin', 'dashboard']))
assert not allow_rule.match(Chain(['a', 'admin', 'secret']))

# ═══════════════════════════════════════════════════════════
# Examples: Log classification
# ═══════════════════════════════════════════════════════════
error_pattern = (
    .rex(r'\d{4}')
    .rex(r'\d{2}')
    .rex(r'\d{2}')
    .ERROR
    .any(0)
)
assert error_pattern.match(Chain(['2024', '01', '15', 'ERROR', 'timeout']))
assert not error_pattern.match(Chain(['2024', '01', '15', 'INFO', 'request']))

# ═══════════════════════════════════════════════════════════
# Guide: Configuration paths
# ═══════════════════════════════════════════════════════════
cfg_rule = .config.database.connection.pool.any(0)
assert cfg_rule.match(Chain(['config', 'database', 'connection', 'pool', '5']))
assert cfg_rule.match(Chain(['config', 'database', 'connection', 'pool']))
assert not cfg_rule.match(Chain(['config', 'database', 'timeout']))

# ═══════════════════════════════════════════════════════════
# Guide: Routing / permissions
# ═══════════════════════════════════════════════════════════
route_rule = .api.v1.enum(
    .users.any(0),
    .admin.un('secret').any(0)
)
assert route_rule.match(Chain(['api', 'v1', 'users', '123']))
assert route_rule.match(Chain(['api', 'v1', 'admin', 'dashboard']))
assert not route_rule.match(Chain(['api', 'v1', 'admin', 'secret']))
assert not route_rule.match(Chain(['api', 'v2', 'users', '123']))

# ═══════════════════════════════════════════════════════════
# Guide: Log level filtering
# ═══════════════════════════════════════════════════════════
log_rule = (
    .rex(r'\d{4}')
    .rex(r'\d{2}')
    .rex(r'\d{2}')
    .enum(
        .ERROR,
        .CRITICAL
    )
    .any(0)
)
assert log_rule.match(Chain(['2024', '01', '15', 'ERROR', 'timeout']))
assert not log_rule.match(Chain(['2024', '01', '15', 'INFO', 'request']))
assert log_rule.match(Chain(['2024', '01', '15', 'CRITICAL', 'oom']))

# ═══════════════════════════════════════════════════════════
# Guide: Optional features (ext)
# ═══════════════════════════════════════════════════════════
rule_ext = .item.rex(r'\d+').ext(.details)
assert rule_ext.match(Chain(['item', '42']))
assert rule_ext.match(Chain(['item', '42', 'details']))
assert not rule_ext.match(Chain(['item', '42', 'extra']))

# ═══════════════════════════════════════════════════════════
# Guide: Custom validation (apply)
# ═══════════════════════════════════════════════════════════
rule_apply = .user.rex(r'[a-z]+').apply(
    lambda seg: int(str(seg).lstrip('.')) > 0
)
assert rule_apply.match(Chain(['user', 'alice', '42']))
assert not rule_apply.match(Chain(['user', 'alice', '0']))
assert not rule_apply.match(Chain(['user', 'alice', '-1']))

# ═══════════════════════════════════════════════════════════
# Guide: any vs ext
# ═══════════════════════════════════════════════════════════
r_any0_b = .any(0).b
assert r_any0_b.match(Chain(['a', 'b']))
assert r_any0_b.match(Chain(['x', 'y', 'b']))
assert r_any0_b.match(Chain(['b']))

r_a_ext_a_b = .a.ext(.a).b
assert r_a_ext_a_b.match(Chain(['a', 'b']))
assert not r_a_ext_a_b.match(Chain(['a', 'x', 'b']))

# ═══════════════════════════════════════════════════════════
# Guide: Migration
# ═══════════════════════════════════════════════════════════
data_mig = .user.profile
rule_mig = .any(0).admin
assert data_mig == Chain(['user', 'profile'])
assert rule_mig == Chain([ChainPatternAtom.any(0), 'admin'])

print("✅ All sugar doc examples passed!")
