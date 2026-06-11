"""Core API tests — uses explicit Chain([...]) and ChainRuleAtom.xxx() directly.
No import hook needed; works in any Python environment.
"""

import sys
sys.path.insert(0, 'src')

from latychain import Chain, ChainRuleAtom


# ═══════════════════════════════════════════════════════════
# Chain basics
# ═══════════════════════════════════════════════════════════

def test_chain_basics():
    c = Chain(['a', 'b', 'c'])
    assert len(c) == 3
    assert c[0] == 'a'
    assert c[-1] == 'c'
    assert list(c) == ['a', 'b', 'c']
    assert list(reversed(c)) == ['c', 'b', 'a']
    assert c.elements == ('a', 'b', 'c')


def test_chain_empty():
    c = Chain()
    assert len(c) == 0
    assert str(c) == '.'
    assert repr(c) == "Chain([])"
    assert bool(c) is False


def test_chain_str():
    assert str(Chain(['a', 'b'])) == '.a.b'
    assert str(Chain(['hello', 'world'])) == '.hello.world'


def test_chain_repr():
    assert repr(Chain(['a', 'b'])) == "Chain(['a', 'b'])"


def test_chain_eq():
    assert Chain(['a', 'b']) == Chain(['a', 'b'])
    assert Chain(['a']) != Chain(['b'])
    assert Chain() == Chain()


def test_chain_hash():
    d = {Chain(['a']): 1, Chain(['b']): 2}
    assert d[Chain(['a'])] == 1
    assert d[Chain(['b'])] == 2


def test_chain_concat():
    result = Chain(['a', 'b']) + Chain(['c', 'd'])
    assert result == Chain(['a', 'b', 'c', 'd'])
    assert result.elements == ('a', 'b', 'c', 'd')


def test_chain_startswith():
    assert Chain(['a', 'b', 'c']).startswith(Chain(['a', 'b']))
    assert Chain(['a', 'b', 'c']).startswith(Chain(['a']))
    assert not Chain(['a', 'b', 'c']).startswith(Chain(['b']))
    assert Chain([]).startswith(Chain([]))


def test_chain_to_list():
    assert Chain(['a', 'b']).to_list() == ['a', 'b']
    assert Chain().to_list() == []


# ═══════════════════════════════════════════════════════════
# Match — basic
# ═══════════════════════════════════════════════════════════

def test_match_exact_string():
    """String in pattern matches identical string in data."""
    assert Chain(['a', 'b']).match(Chain(['a', 'b']))


def test_match_single_any():
    """any(0) matches zero or more arbitrary elements."""
    pat = Chain([ChainRuleAtom.any(0), 'end'])
    assert Chain(['end']).match(pat), "any(0) match zero"
    assert Chain(['x', 'end']).match(pat), "any(0) match one"
    assert Chain(['x', 'y', 'end']).match(pat), "any(0) match two"
    assert not Chain(['x', 'y']).match(pat), "no trailing end"


def test_match_any_min1():
    """any(1) requires at least one element."""
    pat = Chain([ChainRuleAtom.any(1), 'end'])
    assert Chain(['x', 'end']).match(pat), "any(1) match one"
    assert Chain(['x', 'y', 'end']).match(pat), "any(1) match two"
    assert not Chain(['end']).match(pat), "any(1) fail: need at least one before end"


def test_match_any_bounded():
    """any(1, 2) matches between 1 and 2 elements."""
    pat = Chain([ChainRuleAtom.any(1, 2), 'end'])
    assert Chain(['x', 'end']).match(pat), "any(1,2) match one"
    assert Chain(['x', 'y', 'end']).match(pat), "any(1,2) match two"
    assert not Chain(['x', 'y', 'z', 'end']).match(pat), "any(1,2) fail: too many"


def test_match_regex():
    """rex matches a single element via regex fullmatch."""
    pat = Chain([ChainRuleAtom.rex(r'h[12]')])
    assert Chain(['h1']).match(pat)
    assert Chain(['h2']).match(pat)
    assert not Chain(['h3']).match(pat)
    assert not Chain(['h12']).match(pat), "fullmatch required"


def test_match_regex_with_prefix():
    pat = Chain([ChainRuleAtom.any(0), ChainRuleAtom.rex(r'x\d')])
    assert Chain(['a', 'x1']).match(pat)
    assert Chain(['x1']).match(pat)
    assert not Chain(['a', 'xabc']).match(pat)


# ═══════════════════════════════════════════════════════════
# Match — enum
# ═══════════════════════════════════════════════════════════

def test_enum_simple():
    """enum picks one alternative."""
    pat = Chain([ChainRuleAtom.enum(
        Chain(['type', 'h1']),
        Chain(['type', 'h2']),
    )])
    assert Chain(['type', 'h1']).match(pat)
    assert Chain(['type', 'h2']).match(pat)
    assert not Chain(['type', 'h3']).match(pat)


def test_enum_with_any():
    """enum alternatives can contain any()."""
    pat = Chain([ChainRuleAtom.enum(
        Chain(['user', ChainRuleAtom.any(0)]),
        Chain(['admin', ChainRuleAtom.any(0)]),
    )])
    assert Chain(['user', 'login', 'abc']).match(pat)
    assert Chain(['admin', 'delete']).match(pat)
    assert Chain(['user']).match(pat), "any(0) after user matches zero"
    assert not Chain(['guest']).match(pat)


def test_enum_combined_with_any():
    """any(0) before enum, enum consumes rest."""
    pat = Chain([ChainRuleAtom.any(0), ChainRuleAtom.enum(
        Chain(['hi', ChainRuleAtom.rex(r'x[0-9]')]),
        Chain(['wuhu', ChainRuleAtom.apply(lambda c: str(c).startswith('.x'))]),
    )])
    assert Chain(['pre', 'hi', 'x5']).match(pat), "any eats 'pre', enum matches hi+x5"
    assert Chain(['hi', 'x5']).match(pat), "any eats nothing, enum matches hi+x5"
    assert not Chain(['hi', 'abc']).match(pat), "regex fails"


# ═══════════════════════════════════════════════════════════
# Match — apply
# ═══════════════════════════════════════════════════════════

def test_apply_single():
    """apply with long=1 passes a single-element Chain to func."""
    pat = Chain([ChainRuleAtom.apply(lambda c: str(c) == '.abc')])
    assert Chain(['abc']).match(pat)
    assert not Chain(['xyz']).match(pat)


def test_apply_long2():
    """apply with long=2 passes two elements as a Chain."""
    pat = Chain([ChainRuleAtom.apply(lambda c: len(c) == 2, long=2)])
    assert Chain(['a', 'b']).match(pat), "two elements: len(chain)=2"
    assert not Chain(['a']).match(pat), "single element too short"


def test_apply_check_length():
    """apply can check string length via str()."""
    pat = Chain([ChainRuleAtom.apply(lambda c: len(str(c)) > 5)])
    # Chain(['abcde']) -> str = '.abcde' -> len=6 > 5
    assert Chain(['abcde']).match(pat)
    assert not Chain(['a']).match(pat)


# ═══════════════════════════════════════════════════════════
# Match — long
# ═══════════════════════════════════════════════════════════

def test_long_exact():
    pat = Chain([ChainRuleAtom.long(3)])
    assert Chain(['abc']).match(pat)
    assert not Chain(['ab']).match(pat)
    assert not Chain(['abcd']).match(pat)


def test_long_range():
    pat = Chain([ChainRuleAtom.long(2, 4)])
    assert Chain(['ab']).match(pat)
    assert Chain(['abc']).match(pat)
    assert Chain(['abcd']).match(pat)
    assert not Chain(['a']).match(pat)
    assert not Chain(['abcde']).match(pat)


# ═══════════════════════════════════════════════════════════
# Match — un (negation)
# ═══════════════════════════════════════════════════════════

def test_un_simple():
    pat = Chain([ChainRuleAtom.un('admin')])
    assert Chain(['user']).match(pat)
    assert Chain(['guest']).match(pat)
    assert not Chain(['admin']).match(pat)


# ═══════════════════════════════════════════════════════════
# Match — ext (optional)
# ═══════════════════════════════════════════════════════════

def test_ext_optional():
    """ext marks a segment as optional."""
    pat = Chain(['a', ChainRuleAtom.ext(Chain(['pi'])), 'b'])
    assert Chain(['a', 'b']).match(pat), "ext skipped"
    assert Chain(['a', 'pi', 'b']).match(pat), "ext matched"
    assert not Chain(['a', 'x', 'b']).match(pat), "ext partial match fail"


def test_ext_empty():
    """ext() with no argument matches nothing (always skips)."""
    pat = Chain(['a', ChainRuleAtom.ext(), 'b'])
    assert Chain(['a', 'b']).match(pat)
    assert not Chain(['a', 'x', 'b']).match(pat)


# ═══════════════════════════════════════════════════════════
# Match — partial
# ═══════════════════════════════════════════════════════════

def test_partial_match():
    data = Chain(['a', 'b', 'c', 'd'])
    assert data.match(Chain(['a', 'b']), partial=True)
    assert not data.match(Chain(['a', 'b']), partial=False), \
        "partial=False requires full consumption"


def test_partial_with_any():
    data = Chain(['a', 'b', 'c'])
    pat = Chain([ChainRuleAtom.any(0), 'b'])
    assert data.match(pat, partial=True), "any+b matches prefix a,b"
    assert not data.match(pat, partial=False), "does not consume c"


# ═══════════════════════════════════════════════════════════
# Match — edge cases
# ═══════════════════════════════════════════════════════════

def test_empty_data():
    assert Chain().match(Chain([])), "empty matches empty"
    assert Chain().match(Chain([ChainRuleAtom.any(0)]))
    assert not Chain().match(Chain([ChainRuleAtom.any(1)])), "any(1) needs data"


def test_empty_pattern():
    """Empty pattern matches everything (partial) or nothing (full)."""
    data = Chain(['a', 'b'])
    assert data.match(Chain([]), partial=True)
    assert not data.match(Chain([]), partial=False), "empty pattern consumes zero"


# ═══════════════════════════════════════════════════════════
# Run (executed on import)
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
print(f'Core API: {_count} passed, {_fail} failed')
