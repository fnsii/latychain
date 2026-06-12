"""Verify all explicit-API code snippets from README.md are executable."""

from latychain import Chain, ChainPatternAtom, Patom


def test_intro_banner():
    """Top banner — data chain, rule chain, matching."""
    data = Chain(['heading', 'h1'])
    rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])
    assert rule.match(data) is False
    assert rule.match(Chain(['pre', 'uuu', 'x1'])) is True


def test_chain_basics():
    """Chain section — construction, ops, matching."""
    c = Chain(['a', 'b', 'c'])
    assert len(c) == 3
    assert c[0] == 'a'
    assert (c / "d") == Chain(['a', 'b', 'c', 'd'])
    assert str(c) == '.a.b.c'
    assert c.to_list() == ['a', 'b', 'c']
    assert Chain(['a', 'b']).match(c) is False
    assert Chain(['a', 'b']).match(c, partial=True) is True


def test_atom_any():
    rule = Chain([ChainPatternAtom.any(0), 'yyy'])
    assert rule.match(Chain(['x', 'yyy'])) is True
    assert rule.match(Chain(['yyy'])) is True


def test_atom_rex():
    assert Chain([ChainPatternAtom.rex(r'h[12]')]).match(Chain(['h1'])) is True
    assert Chain([ChainPatternAtom.rex(r'\d+')]).match(Chain(['123'])) is True


def test_atom_enum():
    rule = Chain([ChainPatternAtom.enum(
        Chain(['user', ChainPatternAtom.any(0)]),
        Chain(['admin', ChainPatternAtom.any(0)]),
    )])
    assert rule.match(Chain(['user', 'login'])) is True
    assert rule.match(Chain(['guest'])) is False


def test_atom_ext():
    rule = Chain(['a', ChainPatternAtom.ext(Chain(['pi'])), 'b'])
    assert rule.match(Chain(['a', 'b'])) is True
    assert rule.match(Chain(['a', 'pi', 'b'])) is True
    assert rule.match(Chain(['a', 'x', 'b'])) is False


def test_atom_apply():
    rule = Chain([ChainPatternAtom.apply(lambda c: str(c).startswith('.x'))])
    assert rule.match(Chain(['xhello'])) is True


def test_atom_len():
    assert Chain([ChainPatternAtom.len(3)]).match(Chain(['abc'])) is True
    assert Chain([ChainPatternAtom.len(2, 5)]).match(Chain(['abc'])) is True


def test_atom_un():
    assert Chain([ChainPatternAtom.un('admin')]).match(Chain(['user'])) is True


ALL_TESTS = [
    test_intro_banner,
    test_chain_basics,
    test_atom_any,
    test_atom_rex,
    test_atom_enum,
    test_atom_ext,
    test_atom_apply,
    test_atom_len,
    test_atom_un,
]

if __name__ == '__main__':
    _count = 0
    _fail = 0
    for fn in ALL_TESTS:
        try:
            fn()
            _count += 1
        except AssertionError as e:
            print(f'  FAIL {fn.__name__}: {e}')
            _fail += 1
        except Exception as e:
            print(f'  ERROR {fn.__name__}: {type(e).__name__}: {e}')
            _fail += 1
    print(f'README explicit snippets: {_count} passed, {_fail} failed')
