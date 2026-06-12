r"""Chain — immutable ordered container for chain-structured data and pattern matching.

A :class:`Chain` holds an ordered sequence of elements, where each element is
either a plain **string** (representing data) or a :class:`ChainPatternAtom`
(representing a pattern rule). The :meth:`Chain.match` method provides
backtracking pattern matching against rule chains.

Typical usage::

    from latychain import Chain, ChainPatternAtom

    # Data chain
    data = Chain(['heading', 'h1'])

    # Rule chain
    rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\d')])

    # Matching — pattern.match(data)
    rule.match(Chain(['x', 'uuu', 'x1']))
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
    operations (``/``, etc.) return new :class:`Chain` instances. This makes
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

    # Types that are auto-converted to str via str()
    _AUTO_STR_TYPES = (int, float, bool, bytes)

    def __init__(self, elements: Iterable = ()):
        """Create a chain from *elements* (strings, numbers, and/or ChainPatternAtom).

        Numbers (int, float, bool) are automatically converted to strings.

        Raises
        ------
        TypeError
            If any element cannot be converted to :class:`str` or is not a
            :class:`ChainPatternAtom`.
        """
        processed = []
        for elem in elements:
            if isinstance(elem, ChainPatternAtom):
                processed.append(elem)
            elif isinstance(elem, str):
                processed.append(elem)
            elif isinstance(elem, self._AUTO_STR_TYPES):
                processed.append(str(elem))
            else:
                raise TypeError(
                    f"Chain elements must be str, number, or ChainPatternAtom, got {type(elem).__name__}"
                )
        self._data: Tuple[Union[str, ChainPatternAtom], ...] = tuple(processed)

    @classmethod
    def from_str(cls, dotpath: str) -> Chain:
        """Create a data chain from a dot-separated string.

        Each segment becomes a plain string element. Cannot represent
        :class:`ChainPatternAtom` instances — use explicit construction
        for rule chains.

        Parameters
        ----------
        dotpath : str
            A dot-separated path like ``"a.b.c"`` or ``".a.b.c"``.
            Leading dots are ignored.

        Returns
        -------
        Chain
            A new chain with each segment as an element.

        Examples
        --------
        >>> Chain.from_str('a.b.c')
        Chain(['a', 'b', 'c'])
        >>> Chain.from_str('.a.b.c')
        Chain(['a', 'b', 'c'])
        >>> Chain.from_str('')
        Chain([])
        """
        if not dotpath:
            return cls()
        # Remove leading dot if present
        if dotpath.startswith('.'):
            dotpath = dotpath[1:]
        if not dotpath:
            return cls()
        return cls(dotpath.split('.'))

    # ── Read ──────────────────────────────────────────────

    def __getitem__(self, index):
        """Return element at *index*, or a sub-Chain for slices.

        Parameters
        ----------
        index : int or slice
            Index of the element to retrieve, or a slice.
            Negative indices count from the end of the chain.

        Returns
        -------
        str or ChainPatternAtom or Chain
            The element at the given position (for int index),
            or a new :class:`Chain` containing the sliced elements.

        Examples
        --------
        >>> Chain(['a', 'b', 'c'])[0]
        'a'
        >>> Chain(['a', 'b', 'c'])[-1]
        'c'
        >>> Chain(['a', 'b', 'c'])[0:2]
        Chain(['a', 'b'])
        """
        result = self._data[index]
        if isinstance(index, slice):
            return Chain(result)
        return result

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
            Chain(['a']) / Chain(['b'])     → Chain(['a','b'])

        Parameters
        ----------
        other : str or ChainPatternAtom or Chain
            Element to append, or another Chain to concatenate.

        Returns
        -------
        Chain
            A new chain with *other* appended.
        """
        if isinstance(other, Chain):
            return Chain((*self._data, *other._data))
        return Chain((*self._data, other))

    def __rtruediv__(self, other: Any) -> Chain:
        """Support ``"a" / Chain(['b'])`` — prepend *other*."""
        return Chain((other, *self._data))

    def match(self, data: Chain, partial: bool = False) -> bool:
        """Check whether *data* matches this pattern chain.

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
        data : Chain
            The data chain to match against.
        partial : bool, optional
            If ``True``, the pattern only needs to match a prefix of the data.
            If ``False`` (default), the pattern must consume **all** data
            elements.

        Returns
        -------
        bool
            ``True`` if the data matches this pattern.

        Raises
        ------
        TypeError
            If *data* is not a :class:`Chain` instance.

        Examples
        --------
        >>> from latychain import ChainPatternAtom
        >>> rule = Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\\d')])
        >>> rule.match(Chain(['x', 'uuu', 'x1']))
        True

        Partial match:

        >>> Chain(['x', 'uuu']).match(Chain(['x', 'uuu', 'x1']), partial=True)
        True
        >>> Chain(['x', 'uuu']).match(Chain(['x', 'uuu', 'x1']), partial=False)
        False
        """
        if not isinstance(data, Chain):
            raise TypeError(
                f"match() data must be a Chain instance, got {type(data).__name__}"
            )
        if partial:
            return _can_match(data._data, 0, self._data, 0)
        lengths = _all_backtrack_lengths(data._data, 0, self._data, 0)
        return len(data._data) in lengths

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
