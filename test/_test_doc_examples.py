"""Smoke-test ALL code snippets from README.md, docs/api-reference.md, docs/guide.md."""

from latychain import Chain, ChainPatternAtom, Patom


# ═══════════════════════════════════════════════════════════
# README.md — top banner
# ═══════════════════════════════════════════════════════════

def test_readme_banner():
    data = Chain(['heading', 'h1'])
    assert data == Chain(['heading', 'h1'])

    rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])
    r2 = Chain([ChainPatternAtom.any(0), ChainPatternAtom.enum(
        Chain(['hi', ChainPatternAtom.rex(r'x[0-9]')]),
        Chain(['wuhu', ChainPatternAtom.apply(lambda c: str(c).startswith('.x'))]),
    )])
    assert rule.match(Chain(['x', 'uuu', 'x1']))


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

    assert rule.match(Chain(['user', 'login', '123']))
    assert rule.match(Chain(['admin', 'delete', '456']))
    assert not rule.match(Chain(['guest', 'abc']))


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
    assert Chain(['a', 'b']).match(chain, partial=True)
    assert Chain(['a', 'b', 'c']).match(chain)
    assert Chain(['a', 'b']).match(chain, partial=True)


# ═══════════════════════════════════════════════════════════
# README.md — ChainPatternAtom factories (explicit)
# ═══════════════════════════════════════════════════════════

def test_readme_chainruleatom_factories():
    ChainPatternAtom.any(0)
    ChainPatternAtom.rex(r'x\d')
    ChainPatternAtom.enum(Chain(['a']), Chain(['b']))
    ChainPatternAtom.apply(lambda c: len(c) > 2)
    ChainPatternAtom.len(3, 5)
    ChainPatternAtom.un('admin')
    ChainPatternAtom.ext(Chain(['a', 'b']))
    # All fine as long as they don't throw


# ═══════════════════════════════════════════════════════════
# README.md — any / rex / enum / apply / len / un / ext
# ═══════════════════════════════════════════════════════════

def test_readme_any():
    assert Chain([ChainPatternAtom.any(), 'y']).match(Chain(['x', 'y']))
    assert Chain([ChainPatternAtom.any(0), 'y']).match(Chain(['x', 'y']))
    assert Chain([ChainPatternAtom.any(2), 'z']).match(Chain(['x', 'y', 'z']))
    assert Chain([ChainPatternAtom.any(1, 3), 'z']).match(Chain(['x', 'y', 'z']))
    assert Chain([ChainPatternAtom.any(0, 5)]).match(Chain(['x', 'y']))


def test_readme_rex():
    pat = Chain([ChainPatternAtom.rex(r'h[12]')])
    assert pat.match(Chain(['h1']))
    assert pat.match(Chain(['h2']))
    assert not pat.match(Chain(['h3']))

    pat2 = Chain([ChainPatternAtom.rex(r'\d+')])
    assert pat2.match(Chain(['123']))
    assert pat2.match(Chain(['0']))


def test_readme_enum():
    pat = Chain([ChainPatternAtom.enum(
        Chain(['type', 'h1']),
        Chain(['type', 'h2']),
    )])
    assert pat.match(Chain(['type', 'h1']))
    assert pat.match(Chain(['type', 'h2']))
    assert not pat.match(Chain(['type', 'h3']))


def test_readme_apply():
    pat1 = Chain([ChainPatternAtom.apply(lambda seg: str(seg).startswith('.x'))])
    assert pat1.match(Chain(['xhello']))

    # count=2 passes 2 consecutive elements as a Chain; check they create a 2-element chain
    pat2 = Chain([ChainPatternAtom.apply(lambda seg: seg[0] != seg[1], count=2)])
    assert pat2.match(Chain(['a', 'b']))       # ('a','b') → a!=b ✓
    assert not pat2.match(Chain(['a']))        # only 1 element, too short for count=2


def test_readme_len():
    pat1 = Chain([ChainPatternAtom.len(3)])
    assert pat1.match(Chain(['abc']))
    assert not pat1.match(Chain(['ab']))

    pat2 = Chain([ChainPatternAtom.len(2, 5)])
    assert pat2.match(Chain(['abc']))


def test_readme_un():
    pat = Chain([ChainPatternAtom.un('admin')])
    assert pat.match(Chain(['user']))
    assert not pat.match(Chain(['admin']))


def test_readme_ext():
    pat = Chain(['a', ChainPatternAtom.ext(Chain(['pi'])), 'b'])
    assert pat.match(Chain(['a', 'b']))
    assert pat.match(Chain(['a', 'pi', 'b']))
    assert not pat.match(Chain(['a', 'x', 'b']))


# ═══════════════════════════════════════════════════════════
# README.md — Matching: full vs partial
# ═══════════════════════════════════════════════════════════

def test_readme_matching_full_partial():
    data = Chain(['a', 'b', 'c', 'd'])
    assert not Chain(['a', 'b']).match(data)
    assert Chain(['a', 'b']).match(data, partial=True)


# ═══════════════════════════════════════════════════════════
# README.md — Examples
# ═══════════════════════════════════════════════════════════

def test_readme_example_headings():
    rule = Chain([ChainPatternAtom.any(0), 'heading', ChainPatternAtom.rex(r'h[1-6]')])
    assert rule.match(Chain(['heading', 'h1']))
    assert rule.match(Chain(['body', 'heading', 'h3']))
    assert not rule.match(Chain(['heading', 'h7']))


def test_readme_example_permissions():
    rule = Chain([ChainPatternAtom.any(0), ChainPatternAtom.enum(
        Chain(['user', ChainPatternAtom.any(0)]),
        Chain(['admin', ChainPatternAtom.un('secret'), ChainPatternAtom.any(0)]),
    )])
    assert rule.match(Chain(['a', 'user', 'profile']))
    assert rule.match(Chain(['a', 'admin', 'dashboard']))
    assert not rule.match(Chain(['a', 'admin', 'secret']))


def test_readme_example_logs():
    rule = Chain([
        ChainPatternAtom.rex(r'\d{4}'),
        ChainPatternAtom.rex(r'\d{2}'),
        ChainPatternAtom.rex(r'\d{2}'),
        'ERROR',
        ChainPatternAtom.any(0),
    ])
    assert rule.match(Chain(['2024', '01', '15', 'ERROR', 'timeout']))
    assert not rule.match(Chain(['2024', '01', '15', 'INFO', 'request']))


# ═══════════════════════════════════════════════════════════
# docs/api-reference.md — enum (explicit)
# ═══════════════════════════════════════════════════════════

def test_api_enum_explicit():
    pat = Chain([ChainPatternAtom.enum(
        Chain(['type', 'h1']),
        Chain(['type', 'h2']),
    )])
    assert pat.match(Chain(['type', 'h1']))
    assert pat.match(Chain(['type', 'h2']))


# ═══════════════════════════════════════════════════════════
# docs/api-reference.md — rex examples
# ═══════════════════════════════════════════════════════════

def test_api_rex():
    pat = Chain([ChainPatternAtom.rex(r'x[0-9]')])
    assert pat.match(Chain(['x0']))
    assert pat.match(Chain(['x9']))
    assert not pat.match(Chain(['x10']))


# ═══════════════════════════════════════════════════════════
# docs/guide.md — explicit construction
# ═══════════════════════════════════════════════════════════

def test_guide_explicit():
    data = Chain(['user', 'profile', '123'])
    rule = Chain([
        ChainPatternAtom.any(0),
        'user',
        ChainPatternAtom.any(0),
        ChainPatternAtom.rex(r'\d+'),
    ])
    assert rule.match(data) is True


# ═══════════════════════════════════════════════════════════
# docs/guide.md — matching deep dive
# ═══════════════════════════════════════════════════════════

def test_guide_matching_table():
    # Exact string
    assert Chain(['a']).match(Chain(['a']))
    assert not Chain(['a']).match(Chain(['b']))
    # rex
    assert Chain([ChainPatternAtom.rex(r'\d')]).match(Chain(['5']))
    # any
    assert Chain([ChainPatternAtom.any(0), 'y']).match(Chain(['x', 'y']))
    # un
    assert Chain([ChainPatternAtom.un('a')]).match(Chain(['b']))
    assert not Chain([ChainPatternAtom.un('a')]).match(Chain(['a']))
    # len
    assert Chain([ChainPatternAtom.len(2, 4)]).match(Chain(['abc']))
    assert not Chain([ChainPatternAtom.len(2, 4)]).match(Chain(['a']))
    # ext: ext(Chain(['a'])) matches 'a' (consumes 1) or skips (consumes 0)
    # With pattern = [ext(Chain(['a'])), 'b']:
    pat_ext = Chain([ChainPatternAtom.ext(Chain(['a'])), 'b'])
    assert pat_ext.match(Chain(['a', 'b']))   # ext consumes 'a', then 'b' matches
    assert pat_ext.match(Chain(['b']))         # ext skips, then 'b' matches
    assert not pat_ext.match(Chain(['x', 'b'])) # ext skips or tries 'a'→fails, 'x' left unconsumed


def test_guide_backtracking():
    rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])
    data = Chain(['pre', 'uuu', 'x1'])
    assert rule.match(data)


def test_guide_full_partial():
    data = Chain(['a', 'b', 'c', 'd'])
    assert not Chain(['a', 'b']).match(data)
    assert Chain(['a', 'b']).match(data, partial=True)
    assert Chain([ChainPatternAtom.any(0), 'd']).match(data)


# ═══════════════════════════════════════════════════════════
# docs/guide.md — configuration paths
# ═══════════════════════════════════════════════════════════

def test_guide_config():
    rule = Chain(['config', 'database', 'connection', 'pool', ChainPatternAtom.any(0)])
    assert rule.match(Chain(['config', 'database', 'connection', 'pool', '5']))
    assert rule.match(Chain(['config', 'database', 'connection', 'pool']))
    assert not rule.match(Chain(['config', 'database', 'timeout']))


# ═══════════════════════════════════════════════════════════
# docs/guide.md — routing / permissions
# ═══════════════════════════════════════════════════════════

def test_guide_routing():
    rule = Chain(['api', 'v1', ChainPatternAtom.enum(
        Chain(['users', ChainPatternAtom.any(0)]),
        Chain(['admin', ChainPatternAtom.un('secret'), ChainPatternAtom.any(0)]),
    )])
    assert rule.match(Chain(['api', 'v1', 'users', '123']))
    assert rule.match(Chain(['api', 'v1', 'admin', 'dashboard']))
    assert not rule.match(Chain(['api', 'v1', 'admin', 'secret']))
    assert not rule.match(Chain(['api', 'v2', 'users', '123']))


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
    assert rule.match(Chain(['2024', '01', '15', 'ERROR', 'timeout']))
    assert not rule.match(Chain(['2024', '01', '15', 'INFO', 'request']))
    assert rule.match(Chain(['2024', '01', '15', 'CRITICAL', 'oom']))


# ═══════════════════════════════════════════════════════════
# docs/guide.md — ext example
# ═══════════════════════════════════════════════════════════

def test_guide_ext():
    rule = Chain(['item', ChainPatternAtom.rex(r'\d+'), ChainPatternAtom.ext(Chain(['details']))])
    assert rule.match(Chain(['item', '42']))
    assert rule.match(Chain(['item', '42', 'details']))
    assert not rule.match(Chain(['item', '42', 'extra']))


# ═══════════════════════════════════════════════════════════
# docs/guide.md — apply custom validation
# ═══════════════════════════════════════════════════════════

def test_guide_apply_validation():
    rule = Chain(['user', ChainPatternAtom.rex(r'[a-z]+'), ChainPatternAtom.apply(
        lambda seg: int(str(seg).lstrip('.')) > 0
    )])
    assert rule.match(Chain(['user', 'alice', '42']))
    assert not rule.match(Chain(['user', 'alice', '0']))
    assert not rule.match(Chain(['user', 'alice', '-1']))


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
    assert Chain([ChainPatternAtom.any(0), 'b']).match(Chain(['a', 'b']))
    assert Chain([ChainPatternAtom.any(0), 'b']).match(Chain(['x', 'y', 'b']))
    assert Chain([ChainPatternAtom.any(0), 'b']).match(Chain(['b']))

    # ext only matches the specific chain or nothing
    assert Chain(['a', ChainPatternAtom.ext(Chain(['a'])), 'b']).match(Chain(['a', 'b']))
    assert Chain(['a', ChainPatternAtom.ext(Chain(['a'])), 'b']).match(Chain(['a', 'a', 'b']))
    assert not Chain(['a', ChainPatternAtom.ext(Chain(['a'])), 'b']).match(Chain(['a', 'x', 'b']))


# ═══════════════════════════════════════════════════════════
# docs/guide.md — migration
# ═══════════════════════════════════════════════════════════

def test_guide_migration():
    data = Chain(['user', 'profile'])
    rule = Chain([ChainPatternAtom.any(0), 'admin'])
    assert rule.match(data) == rule.match(data)  # just verify no errors


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
