"""latychain — chain-structured data and pattern matching with ``.xxx.yyy`` syntax.

Provides two core types:

* :class:`Chain` — an immutable, ordered container whose elements can be
  plain strings (data) or :class:`ChainRuleAtom` instances (pattern rules).
* :class:`ChainRuleAtom` — rule atoms for building pattern chains, with
  factories for ``any``, ``rex``, ``enum``, ``apply``, ``long``, ``un``,
  and ``ext``.

Additionally, importing :mod:`latychain.ChainDotRule` registers a compile-time
**import hook** that transforms the concise ``.xxx.yyy`` syntax into
:class:`Chain` constructor calls.

Quick start
-----------

Using explicit construction (no sugar)::

    from latychain import Chain, ChainRuleAtom

    # Data chain
    data = Chain(['user', 'profile', 'avatar'])

    # Rule chain
    rule = Chain([
        ChainRuleAtom.any(0),
        'user',
        ChainRuleAtom.any(0),
    ])

    # Match
    data.match(rule)   # True

Using the ``.xxx.yyy`` syntax sugar::

    import latychain.ChainDotRule
    from latychain import Chain

    .user.profile.avatar.match(.any(0).user.any(0))   # True

:class:`Chain` features:

- Immutable and hashable — usable as dictionary keys and set members
- ``+`` concatenation returns a new chain
- ``match(rule)`` — backtracking pattern matching
- ``startswith(prefix)`` — prefix checking
- ``to_list()`` — convert to plain list

:class:`ChainRuleAtom` factories:

.. code-block:: python

    ChainRuleAtom.any(min=0, max=0)      # Match N arbitrary elements
    ChainRuleAtom.rex(pattern)           # Regex fullmatch on one element
    ChainRuleAtom.enum(*alternatives)    # Pick one of several chains
    ChainRuleAtom.apply(func, long=1)    # Custom predicate on N elements
    ChainRuleAtom.long(min, max=None)    # String length constraint
    ChainRuleAtom.un(value)              # Not equal to value
    ChainRuleAtom.ext(chain=None)        # Optional segment
"""

from latychain._chain import Chain
from latychain._atoms import ChainRuleAtom

__all__ = [
    "Chain",
    "ChainRuleAtom",
]

__version__ = "0.1.0"
