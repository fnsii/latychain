"""latychain — chain-structured data and pattern matching with ``.xxx.yyy`` syntax.

Provides two core types:

* :class:`Chain` — an immutable, ordered container whose elements can be
  plain strings (data) or :class:`ChainPatternAtom` instances (pattern rules).
* :class:`ChainPatternAtom` — rule atoms for building pattern chains, with
  factories for ``any``, ``rex``, ``enum``, ``apply``, ``len``, ``un``,
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

    # Match — pattern.match(data)
    rule.match(data)   # True

Using the ``.xxx.yyy`` syntax sugar::

    import latychain.ChainDotRule
    from latychain import Chain

    data = .user.profile.avatar
    rule = .any(0).user.any(0)
    rule.match(data)   # True

:class:`Chain` features:

- Immutable and hashable — usable as dictionary keys and set members
- ``/`` construction via pathlib-style syntax (supports Chain concatenation)
- ``match(data)`` — backtracking pattern matching
- ``from_str(dotpath)`` — create chain from dot-separated string
- ``to_list()`` — convert to plain list

:class:`ChainPatternAtom` factories:

.. code-block:: python

    ChainPatternAtom.any(min=1, max=-1)     # Match N arbitrary elements (max=-1 unbounded)
    ChainPatternAtom.rex(pattern)           # Regex fullmatch on one element
    ChainPatternAtom.enum(*alternatives)    # Pick one of several chains or strings
    ChainPatternAtom.apply(func, count=1)   # Custom predicate on N elements
    ChainPatternAtom.len(min, max=None)     # String length constraint
    ChainPatternAtom.un(value)              # Not equal to value
    ChainPatternAtom.ext(chain)             # Optional segment (match or skip)
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
    __version__ = "0.2.1"  # fallback when running from source (not installed)
