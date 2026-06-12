"""latychain — chain-structured data and pattern matching with ``.xxx.yyy`` syntax.

Provides two core types:

* :class:`Chain` — an immutable, ordered container whose elements can be
  plain strings (data) or :class:`ChainPatternAtom` instances (pattern rules).
* :class:`ChainPatternAtom` (alias ``Patom``) — rule atoms for building pattern
  chains, with factories for ``any``, ``rex``, ``enum``, ``apply``, ``len``,
  ``un``, and ``ext``.

Quick start::

    from latychain import Chain, ChainPatternAtom as Patom

    # Build chains
    data = Chain / "user" / "profile" / "123"
    rule = Chain / Patom.any(0) / "user" / Patom.any(0) / Patom.rex(r"\\d+")

    # Match — pattern.match(data)
    rule.match(data)   # True

Using the ``.xxx.yyy`` syntax sugar::

    import latychain.ChainDotRule
    # In another file with # useLatyChain marker:
    # data = .user.profile.123
    # rule = .any(0).user.any(0).rex(r'\\d+')
    # rule.match(data)   # True

:class:`Chain` features:

- Immutable and hashable — usable as dictionary keys and set members
- ``/`` construction via pathlib-style syntax (supports Chain concatenation)
- Numbers auto-converted to strings (``Chain / 123`` → ``Chain(['123'])``)
- ``match(data)`` — backtracking pattern matching
- ``from_str(dotpath)`` — create chain from dot-separated string
- ``to_list()`` — convert to plain list

:class:`Patom` factories:

.. code-block:: python

    Patom.any(min=1, max=-1)     # Match N arbitrary elements (max=-1 unbounded)
    Patom.rex(pattern)           # Regex fullmatch on one element
    Patom.enum(*alternatives)    # Pick one of several chains or strings
    Patom.apply(func, count=1)   # Custom predicate on N elements
    Patom.len(min, max=None)     # String length constraint
    Patom.un(value)              # Not equal to value
    Patom.ext(chain)             # Optional segment (match or skip)
"""

from latychain._chain import Chain
from latychain._atoms import ChainPatternAtom

# Shorthand alias — "Pattern Atom"
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
