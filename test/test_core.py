"""Core API tests — uses explicit Chain([...]) and ChainPatternAtom.xxx() directly.
No import hook needed; works in any Python environment.
"""

import sys
sys.path.insert(0, 'src')

from latychain import Chain, ChainPatternAtom, Patom


# ═══════════════════════════════════════════════════════════
# Chain basics
# ═══════════════════════════════════════════════════════════

def test_patom_is_chainruleatom():
    """Patom is a convenience alias for ChainPatternAtom."""
    assert Patom is ChainPatternAtom
    assert Patom.any is ChainPatternAtom.any
    assert Patom.any() == ChainPatternAtom.any()


def test_chain_basics():
    c = Chain(["a", "b", "c"])
    assert len(c) == 3
    assert c[0] == "a"
    assert c[-1] == "c"
    assert list(c) == ["a", "b", "c"]
    assert list(reversed(c)) == ["c", "b", "a"]
    assert c.elements == ("a", "b", "c")


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


def test_chain_truediv():
    """Chain / 'a' / 'b' appends elements."""
    # class-level: Chain / ...
    c = Chain / "a" / "b" / "c"
    assert c == Chain(["a", "b", "c"])
    # instance-level: Chain() / ...
    c2 = Chain() / "a" / "b"
    assert c2 == Chain(["a", "b"])
    # Chain() / []  still valid
    assert Chain() == Chain([])


def test_chain_rtruediv():
    """'a' / Chain(['b']) prepends."""
    c = "a" / Chain(["b", "c"])
    assert c == Chain(["a", "b", "c"])


def test_chain_truediv_mixed():
    """Chain / string / Patom mixes elements."""
    c = Chain / "user" / Patom.any(0)
    assert len(c) == 2
    assert c[0] == "user"
    assert isinstance(c[1], ChainPatternAtom)


def test_chain_truediv_chain():
    """Chain / Chain concatenates chains."""
    c = Chain(['a', 'b']) / Chain(['c', 'd'])
    assert c == Chain(['a', 'b', 'c', 'd'])
    assert Chain() / Chain(['a']) == Chain(['a'])
    assert Chain(['a']) / Chain() == Chain(['a'])


def test_chain_to_list():
    assert Chain(['a', 'b']).to_list() == ['a', 'b']
    assert Chain().to_list() == []


def test_chain_contains():
    c = Chain(['a', 'b', 'c'])
    assert 'b' in c
    assert 'x' not in c
    assert 'a' in c
    assert 'c' in c


def test_chain_init_rejects_non_string():
    # Numbers are auto-converted to strings
    assert Chain([123]) == Chain(['123'])
    assert Chain([3.14]) == Chain(['3.14'])
    assert Chain([True]) == Chain(['True'])
    # None and other types are rejected
    try:
        Chain([None])
        assert False, "should have raised TypeError"
    except TypeError:
        pass
    try:
        Chain([[1, 2]])
        assert False, "should have raised TypeError"
    except TypeError:
        pass
    # Strings, numbers, and atoms are fine
    Chain(['a', 123, ChainPatternAtom.any()])  # no error


def test_chain_init_accepts_empty():
    Chain()       # no error
    Chain([])     # no error


def test_any_str_default_and_zero():
    """str(_Any) correctly distinguishes any() from any(0)."""
    assert str(ChainPatternAtom.any()) == 'any()'
    assert str(ChainPatternAtom.any(0)) == 'any(0)'
    assert str(ChainPatternAtom.any(2)) == 'any(2)'
    assert str(ChainPatternAtom.any(1, 3)) == 'any(1,3)'


def test_any_max_zero_errors():
    """any(max=0) should raise ValueError."""
    try:
        ChainPatternAtom.any(max=0)
        assert False, "should have raised ValueError"
    except ValueError:
        pass


# ═══════════════════════════════════════════════════════════
# Match — basic (pattern.match(data) direction)
# ═══════════════════════════════════════════════════════════

def test_match_exact_string():
    """String in pattern matches identical string in data."""
    assert Chain(['a', 'b']).match(Chain(['a', 'b']))


def test_match_single_any():
    """any(0) matches zero or more arbitrary elements."""
    pat = Chain([ChainPatternAtom.any(0), 'end'])
    assert pat.match(Chain(['end'])), "any(0) match zero"
    assert pat.match(Chain(['x', 'end'])), "any(0) match one"
    assert pat.match(Chain(['x', 'y', 'end'])), "any(0) match two"
    assert not pat.match(Chain(['x', 'y'])), "no trailing end"


def test_match_any_min1():
    """any(1) requires at least one element."""
    pat = Chain([ChainPatternAtom.any(1), 'end'])
    assert pat.match(Chain(['x', 'end'])), "any(1) match one"
    assert pat.match(Chain(['x', 'y', 'end'])), "any(1) match two"
    assert not pat.match(Chain(['end'])), "any(1) fail: need at least one before end"


def test_match_any_bounded():
    """any(1, 2) matches between 1 and 2 elements."""
    pat = Chain([ChainPatternAtom.any(1, 2), 'end'])
    assert pat.match(Chain(['x', 'end'])), "any(1,2) match one"
    assert pat.match(Chain(['x', 'y', 'end'])), "any(1,2) match two"
    assert not pat.match(Chain(['x', 'y', 'z', 'end'])), "any(1,2) fail: too many"


def test_match_regex():
    """rex matches a single element via regex fullmatch."""
    pat = Chain([ChainPatternAtom.rex(r'h[12]')])
    assert pat.match(Chain(['h1']))
    assert pat.match(Chain(['h2']))
    assert not pat.match(Chain(['h3']))
    assert not pat.match(Chain(['h12'])), "fullmatch required"


def test_match_regex_with_prefix():
    pat = Chain([ChainPatternAtom.any(0), ChainPatternAtom.rex(r'x\d')])
    assert pat.match(Chain(['a', 'x1']))
    assert pat.match(Chain(['x1']))
    assert not pat.match(Chain(['a', 'xabc']))


# ═══════════════════════════════════════════════════════════
# Match — enum
# ═══════════════════════════════════════════════════════════

def test_enum_simple():
    """enum picks one alternative."""
    pat = Chain([ChainPatternAtom.enum(
        Chain(['type', 'h1']),
        Chain(['type', 'h2']),
    )])
    assert pat.match(Chain(['type', 'h1']))
    assert pat.match(Chain(['type', 'h2']))
    assert not pat.match(Chain(['type', 'h3']))


def test_enum_with_any():
    """enum alternatives can contain any()."""
    pat = Chain([ChainPatternAtom.enum(
        Chain(['user', ChainPatternAtom.any(0)]),
        Chain(['admin', ChainPatternAtom.any(0)]),
    )])
    assert pat.match(Chain(['user', 'login', 'abc']))
    assert pat.match(Chain(['admin', 'delete']))
    assert pat.match(Chain(['user'])), "any(0) after user matches zero"
    assert not pat.match(Chain(['guest']))


def test_enum_combined_with_any():
    """any(0) before enum, enum consumes rest."""
    pat = Chain([ChainPatternAtom.any(0), ChainPatternAtom.enum(
        Chain(['hi', ChainPatternAtom.rex(r'x[0-9]')]),
        Chain(['wuhu', ChainPatternAtom.apply(lambda c: str(c).startswith('.x'))]),
    )])
    assert pat.match(Chain(['pre', 'hi', 'x5'])), "any eats 'pre', enum matches hi+x5"
    assert pat.match(Chain(['hi', 'x5'])), "any eats nothing, enum matches hi+x5"
    assert not pat.match(Chain(['hi', 'abc'])), "regex fails"


def test_enum_with_strings():
    """enum accepts strings directly, auto-wraps into Chains."""
    pat = Chain([ChainPatternAtom.enum('h1', 'h2', 'h3')])
    assert pat.match(Chain(['h1']))
    assert pat.match(Chain(['h2']))
    assert pat.match(Chain(['h3']))
    assert not pat.match(Chain(['h4']))


# ═══════════════════════════════════════════════════════════
# Match — apply
# ═══════════════════════════════════════════════════════════

def test_apply_single():
    """apply with count=1 passes a single-element Chain to func."""
    pat = Chain([ChainPatternAtom.apply(lambda c: str(c) == '.abc')])
    assert pat.match(Chain(['abc']))
    assert not pat.match(Chain(['xyz']))


def test_apply_count2():
    """apply with count=2 passes two elements as a Chain."""
    pat = Chain([ChainPatternAtom.apply(lambda c: len(c) == 2, count=2)])
    assert pat.match(Chain(['a', 'b'])), "two elements: len(chain)=2"
    assert not pat.match(Chain(['a'])), "single element too short"


def test_apply_check_length():
    """apply can check string length via str()."""
    pat = Chain([ChainPatternAtom.apply(lambda c: len(str(c)) > 5)])
    # Chain(['abcde']) -> str = '.abcde' -> len=6 > 5
    assert pat.match(Chain(['abcde']))
    assert not pat.match(Chain(['a']))


# ═══════════════════════════════════════════════════════════
# Match — len (string length constraint)
# ═══════════════════════════════════════════════════════════

def test_len_exact():
    pat = Chain([ChainPatternAtom.len(3)])
    assert pat.match(Chain(['abc']))
    assert not pat.match(Chain(['ab']))
    assert not pat.match(Chain(['abcd']))


def test_len_range():
    pat = Chain([ChainPatternAtom.len(2, 4)])
    assert pat.match(Chain(['ab']))
    assert pat.match(Chain(['abc']))
    assert pat.match(Chain(['abcd']))
    assert not pat.match(Chain(['a']))
    assert not pat.match(Chain(['abcde']))


# ═══════════════════════════════════════════════════════════
# Match — un (negation)
# ═══════════════════════════════════════════════════════════

def test_un_simple():
    pat = Chain([ChainPatternAtom.un('admin')])
    assert pat.match(Chain(['user']))
    assert pat.match(Chain(['guest']))
    assert not pat.match(Chain(['admin']))


# ═══════════════════════════════════════════════════════════
# Match — ext (optional)
# ═══════════════════════════════════════════════════════════

def test_ext_optional():
    """ext marks a segment as optional."""
    pat = Chain(['a', ChainPatternAtom.ext(Chain(['pi'])), 'b'])
    assert pat.match(Chain(['a', 'b'])), "ext skipped"
    assert pat.match(Chain(['a', 'pi', 'b'])), "ext matched"
    assert not pat.match(Chain(['a', 'x', 'b'])), "ext partial match fail"


def test_ext_with_enum():
    """ext can contain enum."""
    pat = Chain(['a', ChainPatternAtom.ext(ChainPatternAtom.enum('x', 'y')), 'b'])
    assert pat.match(Chain(['a', 'b'])), "ext skipped"
    assert pat.match(Chain(['a', 'x', 'b'])), "ext matched x"
    assert pat.match(Chain(['a', 'y', 'b'])), "ext matched y"
    assert not pat.match(Chain(['a', 'z', 'b'])), "ext no match"


def test_ext_requires_arg():
    """ext() with no argument should raise TypeError."""
    try:
        ChainPatternAtom.ext()
        assert False, "should have raised TypeError"
    except TypeError:
        pass


# ═══════════════════════════════════════════════════════════
# Match — partial
# ═══════════════════════════════════════════════════════════

def test_partial_match():
    data = Chain(['a', 'b', 'c', 'd'])
    assert Chain(['a', 'b']).match(data, partial=True)
    assert not Chain(['a', 'b']).match(data, partial=False), \
        "partial=False requires full consumption"


def test_partial_with_any():
    data = Chain(['a', 'b', 'c'])
    pat = Chain([ChainPatternAtom.any(0), 'b'])
    assert pat.match(data, partial=True), "any+b matches prefix a,b"
    assert not pat.match(data, partial=False), "does not consume c"


# ═══════════════════════════════════════════════════════════
# Match — edge cases
# ═══════════════════════════════════════════════════════════

def test_empty_data():
    assert Chain([]).match(Chain([])), "empty matches empty"
    assert Chain([ChainPatternAtom.any(0)]).match(Chain([]))
    assert not Chain([ChainPatternAtom.any()]).match(Chain([])), "any() needs at least 1 element"
    assert not Chain([ChainPatternAtom.any(1)]).match(Chain([])), "any(1) needs data"


def test_empty_pattern():
    """Empty pattern matches everything (partial) or nothing (full)."""
    data = Chain(['a', 'b'])
    assert Chain([]).match(data, partial=True)
    assert not Chain([]).match(data, partial=False), "empty pattern consumes zero"


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
