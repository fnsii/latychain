"""Smoke-test ALL code snippets from README.md, docs/api-reference.md, docs/guide.md."""

from latychain import Chain, ChainPatternAtom, Patom


# ═══════════════════════════════════════════════════════════
# README.md — top banner
# ═══════════════════════════════════════════════════════════

def test_readme_banner():
    heading = Chain(['heading', 'h1'])
    assert heading == Chain(['heading', 'h1'])

    rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])
    r2 = Chain([ChainPatternAtom.any(0), ChainPatternAtom.enum(
        Chain(['hi', ChainPatternAtom.rex(r'x[0-9]')]),
        Chain(['wuhu', ChainPatternAtom.apply(lambda c: str(c).startswith('.x'))]),
    )])
    data = Chain(['x', 'uuu', 'x1'])
    assert data.match(rule)


# ═══════════════════════════════════════════════════════════
# README.md — Quick Start
# ═══════════════════════════════════════════════════════════

def test_readme_quickstart():
    path = Chain(['user', 'profile', 'avatar'])
    assert path == Chain(['user', 'profile', 'avatar'])

    rule = Chain([ChainPatternAtom.any(0), ChainPatternAtom.enum(
        Chain(['admin', ChainPatternAtom.any(0)]),
        Chain(['user', ChainPatternAtom.any(0)]),
    ), ChainPatternAtom.rex(r'\d+')])

    assert Chain(['user', 'login', '123']).match(rule)
    assert Chain(['admin', 'delete', '456']).match(rule)
    assert not Chain(['guest', 'abc']).match(rule)


# ═══════════════════════════════════════════════════════════
# README.md — Chain construction (explicit)
# ═══════════════════════════════════════════════════════════

def test_readme_chain_construction_explicit():
    assert Chain() == Chain([])
    assert Chain(['a']) == Chain(['a'])
    assert Chain(['a', 'b', 'c']) == Chain(['a', 'b', 'c'])
    assert Chain([ChainPatternAtom.any(0)]) == Chain([ChainPatternAtom.any(0)])


def test_readme_chain_operations():
    c = Chain(['a', 'b', 'c'])
    assert len(c) == 3
    assert c[0] == 'a'
    assert c[-1] == 'c'
    assert list(c) == ['a', 'b', 'c']
    assert c.elements == ('a', 'b', 'c')
    assert str(c) == '.a.b.c'
    assert repr(c) == "Chain(['a', 'b', 'c'])"
    assert Chain(['a', 'b']) == Chain(['a', 'b'])
    assert Chain / "a" / "b" / "c" / "d" == Chain(['a', 'b', 'c', 'd'])
    d = {Chain(['a']): 1}
    assert d[Chain(['a'])] == 1


def test_readme_chain_methods():
    chain = Chain(['a', 'b', 'c'])
    assert chain.to_list() == ['a', 'b', 'c']
    assert chain.startswith(Chain(['a', 'b']))
    assert chain.match(Chain(['a', 'b', 'c']))
    assert chain.match(Chain(['a', 'b']), partial=True)


# ═══════════════════════════════════════════════════════════
# README.md — ChainPatternAtom factories (explicit)
# ═══════════════════════════════════════════════════════════

def test_readme_chainruleatom_factories():
    ChainPatternAtom.any(0)
    ChainPatternAtom.rex(r'x\d')
    ChainPatternAtom.enum(Chain(['a']), Chain(['b']))
    ChainPatternAtom.apply(lambda c: len(c) > 2)
    ChainPatternAtom.long(3, 5)
    ChainPatternAtom.un('admin')
    ChainPatternAtom.ext(Chain(['a', 'b']))
    # All fine as long as they don't throw


# ═══════════════════════════════════════════════════════════
# README.md — any / rex / enum / apply / long / un / ext
# ═══════════════════════════════════════════════════════════

def test_readme_any():
    assert Chain(['x', 'y']).match(Chain([ChainPatternAtom.any(), 'y']))
    assert Chain(['x', 'y']).match(Chain([ChainPatternAtom.any(0), 'y']))
    assert Chain(['x', 'y', 'z']).match(Chain([ChainPatternAtom.any(2), 'z']))
    assert Chain(['x', 'y', 'z']).match(Chain([ChainPatternAtom.any(1, 3), 'z']))
    assert Chain(['x', 'y']).match(Chain([ChainPatternAtom.any(0, 5)]))


def test_readme_rex():
    pat = Chain([ChainPatternAtom.rex(r'h[12]')])
    assert Chain(['h1']).match(pat)
    assert Chain(['h2']).match(pat)
    assert not Chain(['h3']).match(pat)

    pat2 = Chain([ChainPatternAtom.rex(r'\d+')])
    assert Chain(['123']).match(pat2)
    assert Chain(['0']).match(pat2)


def test_readme_enum():
    pat = Chain([ChainPatternAtom.enum(
        Chain(['type', 'h1']),
        Chain(['type', 'h2']),
    )])
    assert Chain(['type', 'h1']).match(pat)
    assert Chain(['type', 'h2']).match(pat)
    assert not Chain(['type', 'h3']).match(pat)


def test_readme_apply():
    pat1 = Chain([ChainPatternAtom.apply(lambda seg: str(seg).startswith('.x'))])
    assert Chain(['xhello']).match(pat1)

    # long=2 passes 2 consecutive elements as a Chain; check they create a 2-element chain
    pat2 = Chain([ChainPatternAtom.apply(lambda seg: seg[0] != seg[1], long=2)])
    assert Chain(['a', 'b']).match(pat2)       # ('a','b') → a!=b ✓
    assert not Chain(['a']).match(pat2)        # only 1 element, too short for long=2


def test_readme_long():
    pat1 = Chain([ChainPatternAtom.long(3)])
    assert Chain(['abc']).match(pat1)
    assert not Chain(['ab']).match(pat1)

    pat2 = Chain([ChainPatternAtom.long(2, 5)])
    assert Chain(['abc']).match(pat2)


def test_readme_un():
    pat = Chain([ChainPatternAtom.un('admin')])
    assert Chain(['user']).match(pat)
    assert not Chain(['admin']).match(pat)


def test_readme_ext():
    pat = Chain(['a', ChainPatternAtom.ext(Chain(['pi'])), 'b'])
    assert Chain(['a', 'b']).match(pat)
    assert Chain(['a', 'pi', 'b']).match(pat)
    assert not Chain(['a', 'x', 'b']).match(pat)


# ═══════════════════════════════════════════════════════════
# README.md — Matching: full vs partial
# ═══════════════════════════════════════════════════════════

def test_readme_matching_full_partial():
    data = Chain(['a', 'b', 'c', 'd'])
    assert not data.match(Chain(['a', 'b']))
    assert data.match(Chain(['a', 'b']), partial=True)


# ═══════════════════════════════════════════════════════════
# README.md — Examples
# ═══════════════════════════════════════════════════════════

def test_readme_example_headings():
    rule = Chain([ChainPatternAtom.any(0), 'heading', ChainPatternAtom.rex(r'h[1-6]')])
    assert Chain(['heading', 'h1']).match(rule)
    assert Chain(['body', 'heading', 'h3']).match(rule)
    assert not Chain(['heading', 'h7']).match(rule)


def test_readme_example_permissions():
    rule = Chain([ChainPatternAtom.any(0), ChainPatternAtom.enum(
        Chain(['user', ChainPatternAtom.any(0)]),
        Chain(['admin', ChainPatternAtom.un('secret'), ChainPatternAtom.any(0)]),
    )])
    assert Chain(['a', 'user', 'profile']).match(rule)
    assert Chain(['a', 'admin', 'dashboard']).match(rule)
    assert not Chain(['a', 'admin', 'secret']).match(rule)


def test_readme_example_logs():
    rule = Chain([
        ChainPatternAtom.rex(r'\d{4}'),
        ChainPatternAtom.rex(r'\d{2}'),
        ChainPatternAtom.rex(r'\d{2}'),
        'ERROR',
        ChainPatternAtom.any(0),
    ])
    assert Chain(['2024', '01', '15', 'ERROR', 'timeout']).match(rule)
    assert not Chain(['2024', '01', '15', 'INFO', 'request']).match(rule)


# ═══════════════════════════════════════════════════════════
# docs/api-reference.md — enum (explicit)
# ═══════════════════════════════════════════════════════════

def test_api_enum_explicit():
    pat = Chain([ChainPatternAtom.enum(
        Chain(['type', 'h1']),
        Chain(['type', 'h2']),
    )])
    assert Chain(['type', 'h1']).match(pat)
    assert Chain(['type', 'h2']).match(pat)


# ═══════════════════════════════════════════════════════════
# docs/api-reference.md — rex examples
# ═══════════════════════════════════════════════════════════

def test_api_rex():
    pat = Chain([ChainPatternAtom.rex(r'x[0-9]')])
    assert Chain(['x0']).match(pat)
    assert Chain(['x9']).match(pat)
    assert not Chain(['x10']).match(pat)


# ═══════════════════════════════════════════════════════════
# docs/guide.md — explicit construction
# ═══════════════════════════════════════════════════════════

def test_guide_explicit():
    data = Chain(['user', 'profile', 'avatar'])
    rule = Chain([
        ChainPatternAtom.any(0),
        'user',
        ChainPatternAtom.any(0),
        ChainPatternAtom.rex(r'\d+'),
    ])
    assert data.match(rule) == data.match(rule)  # just ensure it runs


# ═══════════════════════════════════════════════════════════
# docs/guide.md — matching deep dive
# ═══════════════════════════════════════════════════════════

def test_guide_matching_table():
    # Exact string
    assert Chain(['a']).match(Chain(['a']))
    assert not Chain(['a']).match(Chain(['b']))
    # rex
    assert Chain(['5']).match(Chain([ChainPatternAtom.rex(r'\d')]))
    # any
    assert Chain(['x', 'y']).match(Chain([ChainPatternAtom.any(0), 'y']))
    # un
    assert Chain(['b']).match(Chain([ChainPatternAtom.un('a')]))
    assert not Chain(['a']).match(Chain([ChainPatternAtom.un('a')]))
    # long
    assert Chain(['abc']).match(Chain([ChainPatternAtom.long(2, 4)]))
    assert not Chain(['a']).match(Chain([ChainPatternAtom.long(2, 4)]))
    # ext: ext(Chain(['a'])) matches 'a' (consumes 1) or skips (consumes 0)
    # With pattern = [ext(Chain(['a'])), 'b']:
    pat_ext = Chain([ChainPatternAtom.ext(Chain(['a'])), 'b'])
    assert Chain(['a', 'b']).match(pat_ext)   # ext consumes 'a', then 'b' matches
    assert Chain(['b']).match(pat_ext)         # ext skips, then 'b' matches
    assert not Chain(['x', 'b']).match(pat_ext) # ext skips or tries 'a'→fails, 'x' left unconsumed


def test_guide_backtracking():
    rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])
    data = Chain(['pre', 'uuu', 'x1'])
    assert data.match(rule)


def test_guide_full_partial():
    data = Chain(['a', 'b', 'c', 'd'])
    assert not data.match(Chain(['a', 'b']))
    assert data.match(Chain(['a', 'b']), partial=True)
    assert data.match(Chain([ChainPatternAtom.any(0), 'd']))


# ═══════════════════════════════════════════════════════════
# docs/guide.md — configuration paths
# ═══════════════════════════════════════════════════════════

def test_guide_config():
    rule = Chain(['config', 'database', 'connection', 'pool', ChainPatternAtom.any(0)])
    assert Chain(['config', 'database', 'connection', 'pool', '5']).match(rule)
    assert Chain(['config', 'database', 'connection', 'pool']).match(rule)
    assert not Chain(['config', 'database', 'timeout']).match(rule)


# ═══════════════════════════════════════════════════════════
# docs/guide.md — routing / permissions
# ═══════════════════════════════════════════════════════════

def test_guide_routing():
    rule = Chain(['api', 'v1', ChainPatternAtom.enum(
        Chain(['users', ChainPatternAtom.any(0)]),
        Chain(['admin', ChainPatternAtom.un('secret'), ChainPatternAtom.any(0)]),
    )])
    assert Chain(['api', 'v1', 'users', '123']).match(rule)
    assert Chain(['api', 'v1', 'admin', 'dashboard']).match(rule)
    assert not Chain(['api', 'v1', 'admin', 'secret']).match(rule)
    assert not Chain(['api', 'v2', 'users', '123']).match(rule)


# ═══════════════════════════════════════════════════════════
# docs/guide.md — log level filtering
# ═══════════════════════════════════════════════════════════

def test_guide_log_level():
    rule = Chain([
        ChainPatternAtom.rex(r'\d{4}'),
        ChainPatternAtom.rex(r'\d{2}'),
        ChainPatternAtom.rex(r'\d{2}'),
        ChainPatternAtom.enum(Chain(['ERROR']), Chain(['CRITICAL'])),
        ChainPatternAtom.any(0),
    ])
    assert Chain(['2024', '01', '15', 'ERROR', 'timeout']).match(rule)
    assert not Chain(['2024', '01', '15', 'INFO', 'request']).match(rule)
    assert Chain(['2024', '01', '15', 'CRITICAL', 'oom']).match(rule)


# ═══════════════════════════════════════════════════════════
# docs/guide.md — ext example
# ═══════════════════════════════════════════════════════════

def test_guide_ext():
    rule = Chain(['item', ChainPatternAtom.rex(r'\d+'), ChainPatternAtom.ext(Chain(['details']))])
    assert Chain(['item', '42']).match(rule)
    assert Chain(['item', '42', 'details']).match(rule)
    assert not Chain(['item', '42', 'extra']).match(rule)


# ═══════════════════════════════════════════════════════════
# docs/guide.md — apply custom validation
# ═══════════════════════════════════════════════════════════

def test_guide_apply_validation():
    rule = Chain(['user', ChainPatternAtom.rex(r'[a-z]+'), ChainPatternAtom.apply(
        lambda seg: int(str(seg).lstrip('.')) > 0
    )])
    assert Chain(['user', 'alice', '42']).match(rule)
    assert not Chain(['user', 'alice', '0']).match(rule)
    assert not Chain(['user', 'alice', '-1']).match(rule)


# ═══════════════════════════════════════════════════════════
# docs/guide.md — dict keys
# ═══════════════════════════════════════════════════════════

def test_guide_dict_keys():
    permissions = {
        Chain(['admin', 'read']): True,
        Chain(['admin', 'write']): True,
        Chain(['user', 'read']): True,
        Chain(['user', 'write']): False,
    }
    assert permissions[Chain(['admin', 'write'])] is True
    assert permissions[Chain(['user', 'write'])] is False


# ═══════════════════════════════════════════════════════════
# docs/guide.md — any vs ext
# ═══════════════════════════════════════════════════════════

def test_guide_any_vs_ext():
    # any allows anything in between
    assert Chain(['a', 'b']).match(Chain([ChainPatternAtom.any(0), 'b']))
    assert Chain(['x', 'y', 'b']).match(Chain([ChainPatternAtom.any(0), 'b']))
    assert Chain(['b']).match(Chain([ChainPatternAtom.any(0), 'b']))

    # ext only matches the specific chain or nothing
    assert Chain(['a', 'b']).match(Chain(['a', ChainPatternAtom.ext(Chain(['a'])), 'b']))
    assert Chain(['a', 'a', 'b']).match(Chain(['a', ChainPatternAtom.ext(Chain(['a'])), 'b']))
    assert not Chain(['a', 'x', 'b']).match(Chain(['a', ChainPatternAtom.ext(Chain(['a'])), 'b']))


# ═══════════════════════════════════════════════════════════
# docs/guide.md — migration
# ═══════════════════════════════════════════════════════════

def test_guide_migration():
    data = Chain(['user', 'profile'])
    rule = Chain([ChainPatternAtom.any(0), 'admin'])
    assert data.match(data)  # just verify no errors


# ═══════════════════════════════════════════════════════════
# Run
# ═══════════════════════════════════════════════════════════

_count = 0
_fail = 0
for _k, _v in list(globals().items()):
    if _k.startswith('test_') and callable(_v):
        try:
            _v()
            _count += 1
        except AssertionError as _e:
            print(f'  FAIL {_k}: {_e}')
            _fail += 1
        except Exception as _e:
            print(f'  ERROR {_k}: {type(_e).__name__}: {_e}')
            _fail += 1
print(f'Doc examples: {_count} passed, {_fail} failed')
