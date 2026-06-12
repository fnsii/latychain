"""latychain — chain-structured data and pattern matching with ``.xxx.yyy`` syntax.

Provides two core types:

* :class:`Chain` — an immutable, ordered container whose elements can be
  plain strings (data) or :class:`ChainPatternAtom` instances (pattern rules).
* :class:`ChainPatternAtom` — rule atoms for building pattern chains, with
  factories for ``any``, ``rex``, ``enum``, ``apply``, ``long``, ``un``,
  and ``ext``.

Additionally, importing :mod:`latychain.ChainDotRule` registers a compile-time
**import hook** that transforms the concise ``.xxx.yyy`` syntax into
:class:`Chain` constructor calls.

Quick start
-----------

Using explicit construction (no sugar)::

    from latychain import Chain, ChainPatternAtom

    # Data chain
    data = Chain(['user', 'profile', 'avatar'])

    # Rule chain
    rule = Chain([
        ChainPatternAtom.any(0),
        'user',
        ChainPatternAtom.any(0),
    ])

    # Match
    data.match(rule)   # True

Using the ``.xxx.yyy`` syntax sugar::

    import latychain.ChainDotRule
    from latychain import Chain

    data = .user.profile.avatar
    rule = .any(0).user.any(0)
    data.match(rule)   # True

:class:`Chain` features:

- Immutable and hashable — usable as dictionary keys and set members
- ``+`` concatenation returns a new chain
- ``match(rule)`` — backtracking pattern matching
- ``startswith(prefix)`` — prefix checking
- ``to_list()`` — convert to plain list

:class:`ChainPatternAtom` factories:

.. code-block:: python

    ChainPatternAtom.any(min=0, max=0)      # Match N arbitrary elements
    ChainPatternAtom.rex(pattern)           # Regex fullmatch on one element
    ChainPatternAtom.enum(*alternatives)    # Pick one of several chains
    ChainPatternAtom.apply(func, long=1)    # Custom predicate on N elements
    ChainPatternAtom.long(min, max=None)    # String length constraint
    ChainPatternAtom.un(value)              # Not equal to value
    ChainPatternAtom.ext(chain=None)        # Optional segment
"""

from latychain._chain import Chain
from latychain._atoms import ChainPatternAtom

# Shorthand alias — “Pattern Atom”
Patom = ChainPatternAtom

__all__ = [
    "Chain",
    "ChainPatternAtom",
    "Patom",
]

try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("latychain")
except (ImportError, PackageNotFoundError):
    __version__ = "0.1.0a1"  # fallback when running from source (not installed)
