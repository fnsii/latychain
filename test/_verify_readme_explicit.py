"""Verify all explicit-API code snippets from README.md are executable."""

from latychain import Chain, ChainPatternAtom, Patom


def test_intro_banner():
    """Top banner — data chain, rule chain, matching."""
    data = Chain(['heading', 'h1'])
    rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])
    assert data.match(rule) is False
    assert Chain(['pre', 'uuu', 'x1']).match(rule) is True


def test_chain_basics():
    """Chain section — construction, ops, matching."""
    c = Chain(['a', 'b', 'c'])
    assert len(c) == 3
    assert c[0] == 'a'
    assert (c / "d") == Chain(['a', 'b', 'c', 'd'])
    assert str(c) == '.a.b.c'
    assert c.to_list() == ['a', 'b', 'c']
    assert c.match(Chain(['a', 'b'])) is False
    assert c.match(Chain(['a', 'b']), partial=True) is True
    assert c.startswith(Chain(['a', 'b'])) is True


def test_atom_any():
    rule = Chain([ChainPatternAtom.any(0), 'yyy'])
    assert Chain(['x', 'yyy']).match(rule) is True
    assert Chain(['yyy']).match(rule) is True


def test_atom_rex():
    assert Chain(['h1']).match(Chain([ChainPatternAtom.rex(r'h[12]')])) is True
    assert Chain(['123']).match(Chain([ChainPatternAtom.rex(r'\d+')])) is True


def test_atom_enum():
    rule = Chain([ChainPatternAtom.enum(
        Chain(['user', ChainPatternAtom.any(0)]),
        Chain(['admin', ChainPatternAtom.any(0)]),
    )])
    assert Chain(['user', 'login']).match(rule) is True
    assert Chain(['guest']).match(rule) is False


def test_atom_ext():
    rule = Chain(['a', ChainPatternAtom.ext(Chain(['pi'])), 'b'])
    assert Chain(['a', 'b']).match(rule) is True
    assert Chain(['a', 'pi', 'b']).match(rule) is True
    assert Chain(['a', 'x', 'b']).match(rule) is False


def test_atom_apply():
    rule = Chain([ChainPatternAtom.apply(lambda c: str(c).startswith('.x'))])
    assert Chain(['xhello']).match(rule) is True


def test_atom_long():
    assert Chain(['abc']).match(Chain([ChainPatternAtom.long(3)])) is True
    assert Chain(['abc']).match(Chain([ChainPatternAtom.long(2, 5)])) is True


def test_atom_un():
    assert Chain(['user']).match(Chain([ChainPatternAtom.un('admin')])) is True


ALL_TESTS = [
    test_intro_banner,
    test_chain_basics,
    test_atom_any,
    test_atom_rex,
    test_atom_enum,
    test_atom_ext,
    test_atom_apply,
    test_atom_long,
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
