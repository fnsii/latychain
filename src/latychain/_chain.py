r"""Chain — immutable ordered container for chain-structured data and pattern matching.

A :class:`Chain` holds an ordered sequence of elements, where each element is
either a plain **string** (representing data) or a :class:`ChainPatternAtom`
(representing a pattern rule). The :meth:`Chain.match` method provides
backtracking pattern matching against rule chains.

Typical usage::

    from latychain import Chain, ChainPatternAtom

    # Data chain
    Chain(['heading', 'h1'])

    # Rule chain
    Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])

    # Matching
    Chain(['x', 'uuu', 'x1']).match(Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')]))
    # → True
"""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Tuple, Union, TypeVar, Type

from latychain._atoms import ChainPatternAtom

_C = TypeVar('_C', bound='Chain')


# ═══════════════════════════════════════════════════════
# Metaclass — enables Chain / "xxx" at class level
# ═══════════════════════════════════════════════════════

class _ChainMeta(type):
    """Metaclass so that ``Chain / "xxx"`` works on the class itself."""

    def __truediv__(cls, other):
        return cls([other])


# ═══════════════════════════════════════════════════════════
# Backtracking match engine
# ═══════════════════════════════════════════════════════════

def _backtrack_engine(
    data: tuple,
    data_pos: int,
    pattern: tuple,
    pat_pos: int,
    *,
    collect_all: bool = True,
) -> list[int]:
    """Core backtracking engine used by both full and short-circuit matchers.

    When *collect_all* is ``True`` (default), returns **all** possible consumed
    lengths — used by :meth:`Chain.match` (full match) and by
    :class:`~latychain._atoms._Enum`/:class:`~latychain._atoms._Ext`.

    When *collect_all* is ``False``, returns a list of **one** element (the
    first matched length) and short-circuits — used for prefix/partial checks.
    """
    if pat_pos >= len(pattern):
        return [0]

    elem = pattern[pat_pos]
    results: list[int] = []

    if isinstance(elem, str):
        if data_pos < len(data) and data[data_pos] == elem:
            for rest in _backtrack_engine(data, data_pos + 1, pattern, pat_pos + 1,
                                           collect_all=collect_all):
                results.append(1 + rest)
                if not collect_all:
                    return results
        return results

    if isinstance(elem, ChainPatternAtom):
        for length in elem.match_lengths(data, data_pos):
            for rest in _backtrack_engine(data, data_pos + length, pattern, pat_pos + 1,
                                           collect_all=collect_all):
                results.append(length + rest)
                if not collect_all:
                    return results
        return results

    raise TypeError(f"Invalid pattern element: {type(elem).__name__}")


def _all_backtrack_lengths(
    data: tuple,
    data_pos: int,
    pattern: tuple,
    pat_pos: int,
) -> list[int]:
    """Return ALL possible consumed lengths (delegates to core engine)."""
    return _backtrack_engine(data, data_pos, pattern, pat_pos, collect_all=True)


def _can_match(
    data: tuple,
    data_pos: int,
    pattern: tuple,
    pat_pos: int,
) -> bool:
    """Short-circuit: return ``True`` as soon as any match is found."""
    return len(_backtrack_engine(data, data_pos, pattern, pat_pos, collect_all=False)) > 0


# ═══════════════════════════════════════════════════════════
# Chain
# ═══════════════════════════════════════════════════════════

class Chain(metaclass=_ChainMeta):
    r"""Immutable ordered container for chain-structured data.

    A :class:`Chain` holds an ordered sequence of elements, where each element
    is either a plain **string** (representing data) or a **ChainPatternAtom**
    (representing a pattern rule).

    Chains are **immutable**: once created, they cannot be modified. All
    operations (``+``, etc.) return new :class:`Chain` instances. This makes
    them hashable and safe to use as dictionary keys or set members.

    Parameters
    ----------
    elements : Iterable, optional
        An iterable of strings and/or :class:`ChainPatternAtom` instances.
        Defaults to an empty tuple, creating an empty chain.

    Examples
    --------
    >>> from latychain import Chain, ChainPatternAtom

    Empty chain:

    >>> Chain()
    Chain([])

    Data chain (all strings):

    >>> Chain(['heading', 'h1'])
    Chain(['heading', 'h1'])

    Rule chain (mixed with ChainPatternAtom):

    >>> Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])
    Chain([any(0), 'uuu', rex('x\\d')])

    With the ``.xxx.yyy`` syntax sugar (after ``import latychain.ChainDotRule``):

    >>> .heading.h1  # doctest: +SKIP
    Chain(['heading', 'h1'])
    """

    __slots__ = ('_data',)

    def __init__(self, elements: Iterable = ()):
        """Create a chain from *elements* (strings and/or ChainPatternAtom).

        Raises
        ------
        TypeError
            If any element is not a :class:`str` or :class:`ChainPatternAtom`.
        """
        self._data: Tuple[Union[str, ChainPatternAtom], ...] = tuple(elements)
        for elem in self._data:
            if not isinstance(elem, (str, ChainPatternAtom)):
                raise TypeError(
                    f"Chain elements must be str or ChainPatternAtom, got {type(elem).__name__}"
                )

    # ── Read ──────────────────────────────────────────────

    def __getitem__(self, index: int) -> Union[str, ChainPatternAtom]:
        """Return the element at *index* (supports negative indexing).

        Parameters
        ----------
        index : int
            Index of the element to retrieve. Negative indices count from
            the end of the chain.

        Returns
        -------
        str or ChainPatternAtom
            The element at the given position.
        """
        return self._data[index]

    def __len__(self) -> int:
        """Return the number of elements in the chain.

        Returns
        -------
        int
            The chain length.
        """
        return len(self._data)

    def __iter__(self) -> Iterator[Union[str, ChainPatternAtom]]:
        """Iterate over elements of the chain.

        Yields
        ------
        str or ChainPatternAtom
            Each element in order.
        """
        return iter(self._data)

    @property
    def elements(self) -> Tuple[Union[str, ChainPatternAtom], ...]:
        """Return the internal tuple of elements (read-only).

        Returns
        -------
        tuple of str or ChainPatternAtom
            The underlying data tuple.
        """
        return self._data

    # ── String ────────────────────────────────────────────

    def __str__(self) -> str:
        """Return a dot-separated string representation.

        Returns
        -------
        str
            ``".a.b.c"`` for a three-element chain, ``"."`` for an empty chain.

        Examples
        --------
        >>> str(Chain(['a', 'b', 'c']))
        '.a.b.c'
        >>> str(Chain())
        '.'
        """
        if not self._data:
            return "."
        return "." + ".".join(
            str(e) if not isinstance(e, str) else e
            for e in self._data
        )

    def __repr__(self) -> str:
        """Return a developer-friendly representation.

        Returns
        -------
        str
            ``"Chain(['a', 'b', 'c'])"``
        """
        return f"Chain({list(self._data)!r})"

    # ── Equality & hashing ────────────────────────────────

    def __eq__(self, other: Any) -> bool:
        """Compare two chains by value equality.

        Two chains are equal if they contain the same elements in the same
        order (including :class:`ChainPatternAtom` identity/comparison).

        Parameters
        ----------
        other : Any
            The object to compare with.

        Returns
        -------
        bool
            ``True`` if *other* is a :class:`Chain` with equal elements.
        """
        if isinstance(other, Chain):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        """Return a hash based on the chain's elements.

        Enables use of :class:`Chain` as dictionary keys and set members.

        Returns
        -------
        int
            Hash value.
        """
        return hash(self._data)

    def __bool__(self) -> bool:
        """Return ``True`` if the chain is non-empty.

        Returns
        -------
        bool
            ``True`` if the chain has at least one element.
        """
        return len(self._data) > 0

    def __contains__(self, item: Union[str, ChainPatternAtom]) -> bool:
        """Check if *item* is an element of this chain (by equality).

        Parameters
        ----------
        item : str or ChainPatternAtom
            The element to look for.

        Returns
        -------
        bool
            ``True`` if *item* is in this chain.

        Examples
        --------
        >>> 'b' in Chain(['a', 'b', 'c'])
        True
        >>> 'x' in Chain(['a', 'b', 'c'])
        False
        """
        return item in self._data

    # ── Construction via / ───────────────────────────────

    def __truediv__(self, other: Any) -> Chain:
        """Return a new chain with *other* appended.

        Enables ``pathlib``-style construction::

            Chain() / "a" / "b" / "c"     → Chain(['a','b','c'])
            Chain / "a" / "b"              → Chain(['a','b'])
            chain / "x"                    → Chain([*chain, 'x'])

        Parameters
        ----------
        other : str or ChainPatternAtom
            Element to append.

        Returns
        -------
        Chain
            A new chain with *other* appended.
        """
        return Chain((*self._data, other))

    def __rtruediv__(self, other: Any) -> Chain:
        """Support ``"a" / Chain(['b'])`` — prepend *other*."""
        return Chain((other, *self._data))

    def match(self, pattern: Chain, partial: bool = False) -> bool:
        """Check whether this data chain matches the given pattern.

        Uses exhaustive backtracking: tries all possible match lengths
        for each :class:`ChainPatternAtom` to find a combination that consumes
        all (or a prefix of) data elements.

        The matching is **non-greedy**: :class:`~latychain._atoms._Any` atoms
        try shorter matches first, then longer ones if the rest of the pattern
        fails.

        For ``partial=True`` the engine short-circuits as soon as any match
        is found, without enumerating all alternatives.

        Parameters
        ----------
        pattern : Chain
            The pattern chain to match against. May contain both plain strings
            and :class:`ChainPatternAtom` instances.
        partial : bool, optional
            If ``True``, the pattern only needs to match a prefix of the data.
            If ``False`` (default), the pattern must consume **all** data
            elements.

        Returns
        -------
        bool
            ``True`` if the data matches the pattern.

        Examples
        --------
        >>> from latychain import ChainPatternAtom
        >>> data = Chain(['x', 'uuu', 'x1'])
        >>> pattern = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\\d')])
        >>> data.match(pattern)
        True

        Partial match:

        >>> data.match(Chain(['x', 'uuu']), partial=True)
        True
        >>> data.match(Chain(['x', 'uuu']), partial=False)
        False
        """
        if partial:
            return _can_match(self._data, 0, pattern._data, 0)
        lengths = _all_backtrack_lengths(self._data, 0, pattern._data, 0)
        return len(self._data) in lengths

    # ── Utilities ─────────────────────────────────────────

    def to_list(self) -> list:
        """Convert the chain's elements to a plain Python list.

        Returns
        -------
        list
            A list of strings and/or :class:`ChainPatternAtom` instances.

        Examples
        --------
        >>> Chain(['a', 'b', 'c']).to_list()
        ['a', 'b', 'c']
        """
        return list(self._data)

    def startswith(self, prefix: Chain) -> bool:
        """Check if this chain starts with the given prefix.

        This is equivalent to ``self.match(prefix, partial=True)`` but
        short-circuits on the first feasible match without enumerating all
        alternatives.

        Parameters
        ----------
        prefix : Chain
            The prefix to check.

        Returns
        -------
        bool
            ``True`` if the chain starts with *prefix*.

        Examples
        --------
        >>> Chain(['a', 'b', 'c']).startswith(Chain(['a', 'b']))
        True
        >>> Chain(['a', 'b', 'c']).startswith(Chain(['b']))
        False
        """
        return _can_match(self._data, 0, prefix._data, 0)
