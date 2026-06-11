"""ChainRuleAtom — rule atoms for pattern matching in Chains.

Each atom is immutable, hashable, and produces a list of possible
consumed-element-counts via match_lengths() (shortest first = non-greedy).
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
    """Abstract base for all rule atoms."""

    __slots__ = ()

    def match_lengths(self, data: tuple, pos: int) -> list[int]:
        """Return possible consumed lengths (shortest first).

        Args:
            data: The data chain's _data tuple.
            pos:  Current position in data.

        Returns:
            List of possible lengths (0..N). Empty list = no match.
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
    """Match between min and max arbitrary elements (non-greedy)."""

    __slots__ = ('min', 'max')

    def __init__(self, min: int = 0, max: int = 0):
        """max=0 means unbounded."""
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
    """Match one alternative from a list of Chains."""

    __slots__ = ('alternatives',)

    def __init__(self, alternatives: list):
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

    The predicate receives a Chain object and returns a bool.
    """

    __slots__ = ('func', 'long')

    def __init__(self, func: Callable, long: int = 1):
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
    """Match a single element whose string is NOT equal to value."""

    __slots__ = ('value',)

    def __init__(self, value: str):
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
    """Optional segment: try matching inner chain, or skip (consume 0)."""

    __slots__ = ('chain',)

    def __init__(self, chain=None):
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

ChainRuleAtom.any = staticmethod(lambda min=0, max=0: _Any(min, max))
ChainRuleAtom.rex = staticmethod(lambda pattern: _Rex(pattern))
ChainRuleAtom.enum = staticmethod(lambda *alts: _Enum(list(alts)))
ChainRuleAtom.apply = staticmethod(lambda func, long=1: _Apply(func, long))
ChainRuleAtom.long = staticmethod(lambda min, max=None: _Long(min, max))
ChainRuleAtom.un = staticmethod(lambda value: _Un(value))
ChainRuleAtom.ext = staticmethod(lambda chain=None: _Ext(chain))
