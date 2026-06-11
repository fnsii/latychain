"""Chain — immutable ordered container of str | ChainRuleAtom.

A Chain can hold plain strings (data) and/or ChainRuleAtom instances (rules).
Use .match(pattern) to check whether a data chain matches a pattern chain.
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
    For ChainRuleAtom elements, tries every possible match length
    (shortest first = non-greedy) and recurses.

    Args:
        data:    Data chain's _data tuple (strings only in practice).
        data_pos: Current position in data.
        pattern: Pattern chain's _data tuple (strings | ChainRuleAtom).
        pat_pos: Current position in pattern.

    Returns:
        Total elements consumed from data, or None if no match.
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

    Unlike _backtrack_match (which returns the first/shortest match),
    this explores every feasible match length by trying all branch options.
    Used by _Enum and _Ext to provide the outer backtracking loop with
    more alternatives.
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
    """Immutable ordered container.

    Elements can be plain strings (data) or ChainRuleAtom instances (rules).

    Examples:
        >>> Chain(['a', 'b', 'c'])
        >>> Chain([ChainRuleAtom.any(0), 'b'])
    """

    __slots__ = ('_data',)

    def __init__(self, elements: Iterable = ()):
        self._data: Tuple[Union[str, ChainRuleAtom], ...] = tuple(elements)

    # ── Read ──────────────────────────────────────────────

    def __getitem__(self, index: int) -> Union[str, ChainRuleAtom]:
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[Union[str, ChainRuleAtom]]:
        return iter(self._data)

    @property
    def elements(self) -> Tuple[Union[str, ChainRuleAtom], ...]:
        """Return the internal tuple of elements."""
        return self._data

    # ── String ────────────────────────────────────────────

    def __str__(self) -> str:
        if not self._data:
            return "."
        return "." + ".".join(
            str(e) if not isinstance(e, str) else e
            for e in self._data
        )

    def __repr__(self) -> str:
        return f"Chain({list(self._data)!r})"

    # ── Equality & hashing ────────────────────────────────

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Chain):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._data)

    def __bool__(self) -> bool:
        return len(self._data) > 0

    # ── Operations ────────────────────────────────────────

    def __add__(self, other: Any) -> Chain:
        """Concatenate two chains."""
        if isinstance(other, Chain):
            return Chain([*self._data, *other._data])
        return NotImplemented

    def match(self, pattern: Chain, partial: bool = False) -> bool:
        """Check whether this data chain matches the given pattern.

        Uses exhaustive backtracking: tries all possible match lengths
        to find one that consumes all data elements (or a prefix when
        partial=True).

        Args:
            pattern: The pattern chain to match against.
            partial: If True, pattern only needs to match a prefix.

        Returns:
            True if a match is found.
        """
        lengths = _all_backtrack_lengths(self._data, 0, pattern._data, 0)
        if not lengths:
            return False
        if partial:
            return True
        return len(self._data) in lengths

    # ── Utilities ─────────────────────────────────────────

    def to_list(self) -> list:
        """Convert elements to a plain list."""
        return list(self._data)

    def startswith(self, prefix: Chain) -> bool:
        """Check if this chain starts with the given prefix."""
        lengths = _all_backtrack_lengths(self._data, 0, prefix._data, 0)
        return len(lengths) > 0
