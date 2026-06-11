"""ChainRuleAtom — rule atoms for pattern matching in Chains.

Each atom is immutable, hashable, and produces a list of possible
consumed-element-counts via :meth:`ChainRuleAtom.match_lengths`
(shortest first = non-greedy).

Available atoms (created via :class:`ChainRuleAtom` static methods):

.. code-block:: python

    ChainRuleAtom.any(min=0, max=0)      # Match N arbitrary elements
    ChainRuleAtom.rex(pattern)           # Regex fullmatch on a single element
    ChainRuleAtom.enum(*alternatives)    # Pick one of several alternatives
    ChainRuleAtom.apply(func, long=1)    # Custom predicate on N elements
    ChainRuleAtom.long(min, max=None)    # String length constraint
    ChainRuleAtom.un(value)              # Negation: not equal to value
    ChainRuleAtom.ext(chain=None)        # Optional segment (match or skip)
"""

from __future__ import annotations

import re
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from latychain._chain import Chain


# ═══════════════════════════════════════════════════════════
# Base
# ═══════════════════════════════════════════════════════════

class ChainRuleAtom:
    """Abstract base for all rule atoms.

    Every rule atom subclass must implement :meth:`match_lengths`, which
    returns a list of possible numbers of elements this atom could consume
    from the data at a given position (shortest first = non-greedy
    priority).

    Atoms are **immutable** and **hashable**, so they can be stored in
    :class:`~latychain._chain.Chain` objects and used as dictionary keys.
    """

    __slots__ = ()

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        """Return possible consumed lengths (shortest first).

        Subclasses must override this method.

        Parameters
        ----------
        data : tuple
            The data chain's ``_data`` tuple of strings.
        pos : int
            Current position in the data.

        Returns
        -------
        list of int
            List of possible lengths this atom could consume at *pos*.
            An empty list means no match is possible at this position.
            Lengths are sorted in ascending order (non-greedy).
        """
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"<{self}>"


# ═══════════════════════════════════════════════════════════
# _Any — match any N elements (with backtracking)
# ═══════════════════════════════════════════════════════════

class _Any(ChainRuleAtom):
    """Match between *min* and *max* arbitrary data elements.

    Returns all possible consumed lengths in range [*min*, *upper_bound*],
    sorted ascending (non-greedy priority). When *max* is 0, the upper
    bound is unlimited (up to remaining data length).
    """

    __slots__ = ('min', 'max')

    def __init__(self, min: int = 0, max: int = 0):
        """*max* = 0 means unbounded (match any remaining elements)."""
        self.min = min
        self.max = max

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        remaining = len(data) - pos
        if remaining < self.min:
            return []
        upper = min(remaining, self.max) if self.max > 0 else remaining
        return list(range(self.min, upper + 1))

    def __str__(self) -> str:
        if self.max == 0:
            if self.min == 0:
                return "any()"
            return f"any(min={self.min})"
        return f"any({self.min},{self.max})"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, _Any)
                and self.min == other.min
                and self.max == other.max)

    def __hash__(self) -> int:
        return hash(('_Any', self.min, self.max))


# ═══════════════════════════════════════════════════════════
# _Rex — regex fullmatch on a single element
# ═══════════════════════════════════════════════════════════

class _Rex(ChainRuleAtom):
    """Match a single string element via regex fullmatch."""

    __slots__ = ('pattern', '_compiled')

    def __init__(self, pattern: str):
        """
        Parameters
        ----------
        pattern : str
            A regular expression pattern. Will be compiled with
            :func:`re.compile` and used with :meth:`re.Pattern.fullmatch`.
        """
        self.pattern = pattern
        self._compiled = re.compile(pattern)

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        if (pos < len(data)
                and isinstance(data[pos], str)
                and self._compiled.fullmatch(data[pos])):
            return [1]
        return []

    def __str__(self) -> str:
        return f"rex({self.pattern!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Rex) and self.pattern == other.pattern

    def __hash__(self) -> int:
        return hash(('_Rex', self.pattern))


# ═══════════════════════════════════════════════════════════
# _Enum — pick one of several alternatives
# ═══════════════════════════════════════════════════════════

class _Enum(ChainRuleAtom):
    """Match one alternative from a list of Chains.

    Each alternative is a :class:`~latychain._chain.Chain` (which can itself
    contain both strings and :class:`ChainRuleAtom` instances).
    """

    __slots__ = ('alternatives',)

    def __init__(self, alternatives: list):
        """
        Parameters
        ----------
        alternatives : list of Chain
            The list of alternative chains to try.
        """
        self.alternatives = tuple(alternatives)

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        from latychain._chain import _all_backtrack_lengths
        results: list[int] = []
        for alt in self.alternatives:
            results.extend(_all_backtrack_lengths(data, pos, alt._data, 0))
        return sorted(set(results))

    def __str__(self) -> str:
        return f"enum({', '.join(str(a) for a in self.alternatives)})"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, _Enum)
                and self.alternatives == other.alternatives)

    def __hash__(self) -> int:
        return hash(('_Enum', self.alternatives))


# ═══════════════════════════════════════════════════════════
# _Apply — custom function on N elements
# ═══════════════════════════════════════════════════════════

class _Apply(ChainRuleAtom):
    """Match N elements via a user-supplied predicate.

    The predicate receives a :class:`~latychain._chain.Chain` object of
    *long* consecutive elements and returns a boolean.
    """

    __slots__ = ('func', 'long')

    def __init__(self, func: Callable, long: int = 1):
        """
        Parameters
        ----------
        func : callable
            A callable that takes a :class:`~latychain._chain.Chain` and
            returns ``True`` or ``False``.
        long : int, optional
            Number of consecutive elements to pass to *func* (default 1).
        """
        self.func = func
        self.long = long

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        if pos + self.long > len(data):
            return []
        from latychain._chain import Chain
        segment = Chain(data[pos:pos + self.long])
        return [self.long] if self.func(segment) else []

    def __str__(self) -> str:
        name = getattr(self.func, '__name__', '?')
        if self.long == 1:
            return f"apply({name})"
        return f"apply({name}, long={self.long})"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, _Apply)
                and self.func is other.func
                and self.long == other.long)

    def __hash__(self) -> int:
        return hash(('_Apply', id(self.func), self.long))


# ═══════════════════════════════════════════════════════════
# _Long — string length constraint on a single element
# ═══════════════════════════════════════════════════════════

class _Long(ChainRuleAtom):
    """Match a single element whose string length falls in [min, max]."""

    __slots__ = ('min_len', 'max_len')

    def __init__(self, min_len: int, max_len: Optional[int] = None):
        """
        Parameters
        ----------
        min_len : int
            Minimum string length (inclusive).
        max_len : int, optional
            Maximum string length (inclusive). If ``None``, defaults to
            *min_len* (exact length match).
        """
        self.min_len = min_len
        self.max_len = max_len if max_len is not None else min_len

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        if (pos < len(data)
                and isinstance(data[pos], str)
                and self.min_len <= len(data[pos]) <= self.max_len):
            return [1]
        return []

    def __str__(self) -> str:
        if self.min_len == self.max_len:
            return f"long({self.min_len})"
        return f"long({self.min_len},{self.max_len})"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, _Long)
                and self.min_len == other.min_len
                and self.max_len == other.max_len)

    def __hash__(self) -> int:
        return hash(('_Long', self.min_len, self.max_len))


# ═══════════════════════════════════════════════════════════
# _Un — negation (not equal to a value)
# ═══════════════════════════════════════════════════════════

class _Un(ChainRuleAtom):
    """Match a single element whose string is NOT equal to *value*."""

    __slots__ = ('value',)

    def __init__(self, value: str):
        """
        Parameters
        ----------
        value : str
            The value to negate. Any element that is not equal to this value
            will match.
        """
        self.value = value

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        if pos < len(data) and data[pos] != self.value:
            return [1]
        return []

    def __str__(self) -> str:
        return f"un({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Un) and self.value == other.value

    def __hash__(self) -> int:
        return hash(('_Un', self.value))


# ═══════════════════════════════════════════════════════════
# _Ext — optional segment (try or skip)
# ═══════════════════════════════════════════════════════════

class _Ext(ChainRuleAtom):
    """Optional segment: try matching inner chain, or skip (consume 0).

    Always includes 0 in :meth:`match_lengths`, so the backtracking engine
    can choose to skip this segment entirely. If an inner chain is provided,
    its possible consumed lengths are also included.
    """

    __slots__ = ('chain',)

    def __init__(self, chain=None):
        """
        Parameters
        ----------
        chain : Chain, optional
            The optional chain to try matching. If ``None``, the atom
            always matches 0 elements (effectively a no-op).
        """
        self.chain = chain

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        results: list[int] = [0]
        if self.chain is not None:
            from latychain._chain import _all_backtrack_lengths
            results.extend(_all_backtrack_lengths(data, pos, self.chain._data, 0))
        return sorted(set(results))

    def __str__(self) -> str:
        if self.chain is None:
            return "ext()"
        return f"ext({self.chain})"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, _Ext)
                and self.chain == other.chain)

    def __hash__(self) -> int:
        return hash(('_Ext', id(self.chain)))


# ═══════════════════════════════════════════════════════════
# Factory methods on ChainRuleAtom
# ═══════════════════════════════════════════════════════════

def _any_factory(min: int = 0, max: int = 0) -> ChainRuleAtom:
    """Create an atom that matches between *min* and *max* arbitrary elements.

    Parameters
    ----------
    min : int, optional
        Minimum number of elements to match (default 0).
    max : int, optional
        Maximum number of elements to match. 0 means unbounded (default 0).

    Returns
    -------
    ChainRuleAtom
        An ``_Any`` atom instance.

    Examples
    --------
    >>> ChainRuleAtom.any()       # at least 1, unlimited
    >>> ChainRuleAtom.any(0)      # 0 or more
    >>> ChainRuleAtom.any(2)      # at least 2
    >>> ChainRuleAtom.any(1, 3)   # 1 to 3
    """
    return _Any(min, max)


def _rex_factory(pattern: str) -> ChainRuleAtom:
    """Create an atom that regex-fullmatches a single element.

    Uses :func:`re.compile` and :meth:`re.Pattern.fullmatch` internally.

    Parameters
    ----------
    pattern : str
        Regular expression pattern.

    Returns
    -------
    ChainRuleAtom
        A ``_Rex`` atom instance.

    Examples
    --------
    >>> ChainRuleAtom.rex(r'h[12]')   # matches 'h1', 'h2'
    >>> ChainRuleAtom.rex(r'\\d+')     # matches '123'
    """
    return _Rex(pattern)


def _enum_factory(*alternatives) -> ChainRuleAtom:
    """Create an atom that picks one of several alternatives.

    Parameters
    ----------
    *alternatives : Chain
        One or more :class:`~latychain._chain.Chain` instances to try.
        The first one that fully matches wins.

    Returns
    -------
    ChainRuleAtom
        An ``_Enum`` atom instance.

    Examples
    --------
    >>> ChainRuleAtom.enum(Chain(['a']), Chain(['b']))
    """
    return _Enum(list(alternatives))


def _apply_factory(func: Callable, long: int = 1) -> ChainRuleAtom:
    """Create an atom that matches via a user-supplied function.

    The function receives a :class:`~latychain._chain.Chain` of *long*
    consecutive elements and must return ``True`` or ``False``.

    Parameters
    ----------
    func : callable
        A callable ``(Chain) -> bool``.
    long : int, optional
        Number of consecutive elements to pass to *func* (default 1).

    Returns
    -------
    ChainRuleAtom
        An ``_Apply`` atom instance.
    """
    return _Apply(func, long)


def _long_factory(min: int, max: Optional[int] = None) -> ChainRuleAtom:
    """Create an atom that constrains the string length of a single element.

    Parameters
    ----------
    min : int
        Minimum string length (inclusive).
    max : int, optional
        Maximum string length (inclusive). If ``None``, an exact match
        against *min* is performed.

    Returns
    -------
    ChainRuleAtom
        A ``_Long`` atom instance.

    Examples
    --------
    >>> ChainRuleAtom.long(3)      # exactly 3 characters
    >>> ChainRuleAtom.long(2, 5)   # 2 to 5 characters
    """
    return _Long(min, max)


def _un_factory(value: str) -> ChainRuleAtom:
    """Create an atom that matches any element NOT equal to *value*.

    Parameters
    ----------
    value : str
        The value to reject.

    Returns
    -------
    ChainRuleAtom
        An ``_Un`` atom instance.

    Examples
    --------
    >>> ChainRuleAtom.un('admin')  # matches anything except 'admin'
    """
    return _Un(value)


def _ext_factory(chain=None) -> ChainRuleAtom:
    """Create an optional segment atom.

    Always allows consuming 0 elements (skip). If *chain* is provided, also
    allows consuming whatever *chain* would consume.

    Parameters
    ----------
    chain : Chain, optional
        The optional chain to try matching.

    Returns
    -------
    ChainRuleAtom
        An ``_Ext`` atom instance.

    Examples
    --------
    >>> ChainRuleAtom.ext()               # always skips
    >>> ChainRuleAtom.ext(Chain(['a']))   # matches 'a' or skips
    """
    return _Ext(chain)


# Attach factory methods to ChainRuleAtom
ChainRuleAtom.any = staticmethod(_any_factory)
ChainRuleAtom.rex = staticmethod(_rex_factory)
ChainRuleAtom.enum = staticmethod(_enum_factory)
ChainRuleAtom.apply = staticmethod(_apply_factory)
ChainRuleAtom.long = staticmethod(_long_factory)
ChainRuleAtom.un = staticmethod(_un_factory)
ChainRuleAtom.ext = staticmethod(_ext_factory)
