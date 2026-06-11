"""Test doc examples that use `.xxx.yyy` sugar syntax.

Loaded via import hook (run from _run_doc_sugar.py).
"""

from latychain import Chain, ChainRuleAtom

# ═══════════════════════════════════════════════════════════
# README banner
# ═══════════════════════════════════════════════════════════
heading = .heading.h1
assert heading == Chain(['heading', 'h1'])

rule = .any(0).uuu.rex(r'x\d')
assert rule == Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])

r2 = .any(0).enum(
    .hi.rex(r'x[0-9]'),
    .wuhu.apply(lambda c: str(c).startswith('.x'))
)
assert Chain(['pre', 'hi', 'x5']).match(r2)
assert Chain(['pre', 'wuhu', 'xok']).match(r2)

x = .x.uuu.x1
assert x == Chain(['x', 'uuu', 'x1'])
assert x.match(rule)

# ═══════════════════════════════════════════════════════════
# Quick Start — CORRECT pattern: build data separately, call .match()
# ═══════════════════════════════════════════════════════════
path = .user.profile.avatar
assert path == Chain(['user', 'profile', 'avatar'])

rule2 = .any(0).enum(
    .admin.any(0),
    .user.any(0)
).rex(r'\d+')

assert Chain(['user', 'login', '123']).match(rule2)
assert Chain(['admin', 'delete', '456']).match(rule2)
assert not Chain(['guest', 'abc']).match(rule2)

# ═══════════════════════════════════════════════════════════
# Chain construction (sugar)
# ═══════════════════════════════════════════════════════════
assert .a.b.c == Chain(['a', 'b', 'c'])
assert .any(0).uuu.rex(r'x\d') == Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\d')])

# ═══════════════════════════════════════════════════════════
# any examples
# ═══════════════════════════════════════════════════════════
assert Chain(['x', 'y']).match(.any())        # at least 1
assert Chain(['x', 'y']).match(.any(0))       # 0 or more
assert Chain(['x', 'y', 'z']).match(.any(2))  # at least 2
assert Chain(['x', 'y', 'z']).match(.any(1, 3).z)  # 1-3 then 'z'
assert Chain(['x', 'y']).match(.any(0, 5))    # 0-5

# ═══════════════════════════════════════════════════════════
# rex examples
# ═══════════════════════════════════════════════════════════
assert Chain(['h1']).match(.rex(r'h[12]'))
assert Chain(['h2']).match(.rex(r'h[12]'))
assert not Chain(['h3']).match(.rex(r'h[12]'))
assert Chain(['123']).match(.rex(r'\d+'))
assert Chain(['0']).match(.rex(r'\d+'))

# ═══════════════════════════════════════════════════════════
# enum examples
# ═══════════════════════════════════════════════════════════
enum_pat = .enum(
    .type.h1,
    .type.h2
)
assert Chain(['type', 'h1']).match(enum_pat)
assert Chain(['type', 'h2']).match(enum_pat)
assert not Chain(['type', 'h3']).match(enum_pat)

# ═══════════════════════════════════════════════════════════
# apply examples
# ═══════════════════════════════════════════════════════════
assert Chain(['xhello']).match(.apply(lambda seg: str(seg).startswith('.x')))
assert Chain(['a', 'b']).match(.apply(lambda seg: seg[0] != seg[1], long=2))

# ═══════════════════════════════════════════════════════════
# long examples
# ═══════════════════════════════════════════════════════════
assert Chain(['abc']).match(.long(3))
assert not Chain(['ab']).match(.long(3))
assert Chain(['abc']).match(.long(2, 5))

# ═══════════════════════════════════════════════════════════
# un examples
# ═══════════════════════════════════════════════════════════
assert Chain(['user']).match(.un('admin'))
assert not Chain(['admin']).match(.un('admin'))

# ═══════════════════════════════════════════════════════════
# ext examples
# ═══════════════════════════════════════════════════════════
ext_pat = .a.ext(.pi).b
assert Chain(['a', 'b']).match(ext_pat)
assert Chain(['a', 'pi', 'b']).match(ext_pat)
assert not Chain(['a', 'x', 'b']).match(ext_pat)

# ═══════════════════════════════════════════════════════════
# Full vs partial match
# ═══════════════════════════════════════════════════════════
data = .a.b.c.d
assert not data.match(.a.b)
assert data.match(.a.b, partial=True)
assert data.match(.any(0).d)

# ═══════════════════════════════════════════════════════════
# Examples: HTML headings
# ═══════════════════════════════════════════════════════════
heading_rule = .any(0).heading.rex(r'h[1-6]')
assert Chain(['heading', 'h1']).match(heading_rule)
assert Chain(['body', 'heading', 'h3']).match(heading_rule)
assert not Chain(['heading', 'h7']).match(heading_rule)

# ═══════════════════════════════════════════════════════════
# Examples: Path permissions
# ═══════════════════════════════════════════════════════════
allow_rule = .any(0).enum(
    .user.any(0),
    .admin.un('secret').any(0)
)
assert Chain(['a', 'user', 'profile']).match(allow_rule)
assert Chain(['a', 'admin', 'dashboard']).match(allow_rule)
assert not Chain(['a', 'admin', 'secret']).match(allow_rule)

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
assert Chain(['2024', '01', '15', 'ERROR', 'timeout']).match(error_pattern)
assert not Chain(['2024', '01', '15', 'INFO', 'request']).match(error_pattern)

# ═══════════════════════════════════════════════════════════
# Guide: Configuration paths
# ═══════════════════════════════════════════════════════════
cfg_rule = .config.database.connection.pool.any(0)
assert Chain(['config', 'database', 'connection', 'pool', '5']).match(cfg_rule)
assert Chain(['config', 'database', 'connection', 'pool']).match(cfg_rule)
assert not Chain(['config', 'database', 'timeout']).match(cfg_rule)

# ═══════════════════════════════════════════════════════════
# Guide: Routing / permissions
# ═══════════════════════════════════════════════════════════
route_rule = .api.v1.enum(
    .users.any(0),
    .admin.un('secret').any(0)
)
assert Chain(['api', 'v1', 'users', '123']).match(route_rule)
assert Chain(['api', 'v1', 'admin', 'dashboard']).match(route_rule)
assert not Chain(['api', 'v1', 'admin', 'secret']).match(route_rule)
assert not Chain(['api', 'v2', 'users', '123']).match(route_rule)

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
assert Chain(['2024', '01', '15', 'ERROR', 'timeout']).match(log_rule)
assert not Chain(['2024', '01', '15', 'INFO', 'request']).match(log_rule)
assert Chain(['2024', '01', '15', 'CRITICAL', 'oom']).match(log_rule)

# ═══════════════════════════════════════════════════════════
# Guide: Optional features (ext)
# ═══════════════════════════════════════════════════════════
rule_ext = .item.rex(r'\d+').ext(.details)
assert Chain(['item', '42']).match(rule_ext)
assert Chain(['item', '42', 'details']).match(rule_ext)
assert not Chain(['item', '42', 'extra']).match(rule_ext)

# ═══════════════════════════════════════════════════════════
# Guide: Custom validation (apply)
# ═══════════════════════════════════════════════════════════
rule_apply = .user.rex(r'[a-z]+').apply(
    lambda seg: int(str(seg).lstrip('.')) > 0
)
assert Chain(['user', 'alice', '42']).match(rule_apply)
assert not Chain(['user', 'alice', '0']).match(rule_apply)
assert not Chain(['user', 'alice', '-1']).match(rule_apply)

# ═══════════════════════════════════════════════════════════
# Guide: any vs ext
# ═══════════════════════════════════════════════════════════
assert Chain(['a', 'b']).match(.any(0).b)
assert Chain(['x', 'y', 'b']).match(.any(0).b)
assert Chain(['b']).match(.any(0).b)

assert Chain(['a', 'b']).match(.a.ext(.a).b)
assert not Chain(['a', 'x', 'b']).match(.a.ext(.a).b)

# ═══════════════════════════════════════════════════════════
# Guide: Migration
# ═══════════════════════════════════════════════════════════
data_mig = .user.profile
rule_mig = .any(0).admin
assert data_mig == Chain(['user', 'profile'])
assert rule_mig == Chain([ChainRuleAtom.any(0), 'admin'])

print("✅ All sugar doc examples passed!")
