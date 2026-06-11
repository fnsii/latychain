"""Chain — immutable ordered container for chain-structured data and pattern matching.

A :class:`Chain` holds an ordered sequence of elements, where each element is
either a plain **string** (representing data) or a :class:`ChainRuleAtom`
(representing a pattern rule). The :meth:`Chain.match` method provides
backtracking pattern matching against rule chains.

Typical usage::

    from latychain import Chain, ChainRuleAtom

    # Data chain
    Chain(['heading', 'h1'])

    # Rule chain
    Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\\d')])

    # Matching
    Chain(['x', 'uuu', 'x1']).match(Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\\d')]))
    # → True
"""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Optional, Tuple, Union

from latychain._atoms import ChainRuleAtom


# ═══════════════════════════════════════════════════════════
# Backtracking match engine
# ═══════════════════════════════════════════════════════════

def _backtrack_match(
    data: tuple,
    data_pos: int,
    pattern: tuple,
    pat_pos: int,
) -> Optional[int]:
    """Backtracking sequential matcher.

    Tries each pattern element against the data starting at data_pos.
    For :class:`ChainRuleAtom` elements, tries every possible match length
    (shortest first = non-greedy) and recurses.

    Args:
        data: Data chain's ``_data`` tuple (strings only in practice).
        data_pos: Current position in data.
        pattern: Pattern chain's ``_data`` tuple (strings | ChainRuleAtom).
        pat_pos: Current position in pattern.

    Returns:
        Total elements consumed from data, or ``None`` if no match.
    """
    if pat_pos >= len(pattern):
        return 0

    elem = pattern[pat_pos]

    if isinstance(elem, str):
        if data_pos < len(data) and data[data_pos] == elem:
            rest = _backtrack_match(data, data_pos + 1, pattern, pat_pos + 1)
            return (1 + rest) if rest is not None else None
        return None

    if isinstance(elem, ChainRuleAtom):
        for length in elem.match_lengths(data, data_pos):
            rest = _backtrack_match(data, data_pos + length, pattern, pat_pos + 1)
            if rest is not None:
                return length + rest
        return None

    raise TypeError(f"Invalid pattern element: {type(elem).__name__}")


def _all_backtrack_lengths(
    data: tuple,
    data_pos: int,
    pattern: tuple,
    pat_pos: int,
) -> list[int]:
    """Return ALL possible consumed lengths for matching pattern against data.

    Unlike :func:`_backtrack_match` (which returns the first/shortest match),
    this explores every feasible match length by trying all branch options.

    Used by :class:`~latychain._atoms._Enum` and :class:`~latychain._atoms._Ext`
    to provide the outer backtracking loop with more alternatives.

    Args:
        data: Data chain's ``_data`` tuple.
        data_pos: Current position in data.
        pattern: Pattern chain's ``_data`` tuple.
        pat_pos: Current position in pattern.

    Returns:
        List of all possible consumed lengths (sorted ascending).
    """
    if pat_pos >= len(pattern):
        return [0]

    elem = pattern[pat_pos]
    results: list[int] = []

    if isinstance(elem, str):
        if data_pos < len(data) and data[data_pos] == elem:
            for rest in _all_backtrack_lengths(data, data_pos + 1, pattern, pat_pos + 1):
                results.append(1 + rest)
        return results

    if isinstance(elem, ChainRuleAtom):
        for length in elem.match_lengths(data, data_pos):
            for rest in _all_backtrack_lengths(data, data_pos + length, pattern, pat_pos + 1):
                results.append(length + rest)
        return results

    raise TypeError(f"Invalid pattern element: {type(elem).__name__}")


# ═══════════════════════════════════════════════════════════
# Chain
# ═══════════════════════════════════════════════════════════

class Chain:
    """Immutable ordered container for chain-structured data.

    A :class:`Chain` holds an ordered sequence of elements, where each element
    is either a plain **string** (representing data) or a **ChainRuleAtom**
    (representing a pattern rule).

    Chains are **immutable**: once created, they cannot be modified. All
    operations (``+``, etc.) return new :class:`Chain` instances. This makes
    them hashable and safe to use as dictionary keys or set members.

    Parameters
    ----------
    elements : Iterable, optional
        An iterable of strings and/or :class:`ChainRuleAtom` instances.
        Defaults to an empty tuple, creating an empty chain.

    Examples
    --------
    >>> from latychain import Chain, ChainRuleAtom

    Empty chain:

    >>> Chain()
    Chain([])

    Data chain (all strings):

    >>> Chain(['heading', 'h1'])
    Chain(['heading', 'h1'])

    Rule chain (mixed with ChainRuleAtom):

    >>> Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\\d')])
    Chain([any(0), 'uuu', rex('x\\\\d')])

    With the ``.xxx.yyy`` syntax sugar (after ``import latychain.ChainDotRule``):

    >>> .heading.h1  # doctest: +SKIP
    Chain(['heading', 'h1'])
    """

    __slots__ = ('_data',)

    def __init__(self, elements: Iterable = ()):
        self._data: Tuple[Union[str, ChainRuleAtom], ...] = tuple(elements)

    # ── Read ──────────────────────────────────────────────

    def __getitem__(self, index: int) -> Union[str, ChainRuleAtom]:
        """Return the element at *index* (supports negative indexing).

        Parameters
        ----------
        index : int
            Index of the element to retrieve. Negative indices count from
            the end of the chain.

        Returns
        -------
        str or ChainRuleAtom
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

    def __iter__(self) -> Iterator[Union[str, ChainRuleAtom]]:
        """Iterate over elements of the chain.

        Yields
        ------
        str or ChainRuleAtom
            Each element in order.
        """
        return iter(self._data)

    @property
    def elements(self) -> Tuple[Union[str, ChainRuleAtom], ...]:
        """Return the internal tuple of elements (read-only).

        Returns
        -------
        tuple of str or ChainRuleAtom
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
        order (including :class:`ChainRuleAtom` identity/comparison).

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

    # ── Operations ────────────────────────────────────────

    def __add__(self, other: Any) -> Chain:
        """Concatenate two chains, returning a new chain.

        Parameters
        ----------
        other : Chain
            The chain to append to this one.

        Returns
        -------
        Chain
            A new chain containing elements from both chains.

        Raises
        ------
        TypeError
            If *other* is not a :class:`Chain`.

        Examples
        --------
        >>> Chain(['a', 'b']) + Chain(['c', 'd'])
        Chain(['a', 'b', 'c', 'd'])
        """
        if isinstance(other, Chain):
            return Chain([*self._data, *other._data])
        return NotImplemented

    def match(self, pattern: Chain, partial: bool = False) -> bool:
        """Check whether this data chain matches the given pattern.

        Uses exhaustive backtracking: tries all possible match lengths
        for each :class:`ChainRuleAtom` to find a combination that consumes
        all (or a prefix of) data elements.

        The matching is **non-greedy**: :class:`~latychain._atoms._Any` atoms
        try shorter matches first, then longer ones if the rest of the pattern
        fails.

        Parameters
        ----------
        pattern : Chain
            The pattern chain to match against. May contain both plain strings
            and :class:`ChainRuleAtom` instances.
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
        >>> from latychain import ChainRuleAtom
        >>> data = Chain(['x', 'uuu', 'x1'])
        >>> pattern = Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\\d')])
        >>> data.match(pattern)
        True

        Partial match:

        >>> data.match(Chain(['x', 'uuu']), partial=True)
        True
        >>> data.match(Chain(['x', 'uuu']), partial=False)
        False
        """
        lengths = _all_backtrack_lengths(self._data, 0, pattern._data, 0)
        if not lengths:
            return False
        if partial:
            return True
        return len(self._data) in lengths

    # ── Utilities ─────────────────────────────────────────

    def to_list(self) -> list:
        """Convert the chain's elements to a plain Python list.

        Returns
        -------
        list
            A list of strings and/or :class:`ChainRuleAtom` instances.

        Examples
        --------
        >>> Chain(['a', 'b', 'c']).to_list()
        ['a', 'b', 'c']
        """
        return list(self._data)

    def startswith(self, prefix: Chain) -> bool:
        """Check if this chain starts with the given prefix.

        This is equivalent to ``self.match(prefix, partial=True)``.

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
        lengths = _all_backtrack_lengths(self._data, 0, prefix._data, 0)
        return len(lengths) > 0
