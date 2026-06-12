"""Import hook to enable ``.xxx.yyy`` syntax sugar.

Once imported, modules that contain ``# useLatyChain`` in their first few lines
have their ``.xxx.yyy.zzz()`` expressions automatically transformed into
``Chain([...])`` calls at compile time.

``Chain`` and ``ChainPatternAtom`` (and shorthand ``Patom``) are
**auto-injected** into marked modules, so no explicit import is needed.

Usage::

    # my_logic.py — uses sugar (requires # useLatyChain marker)
    # useLatyChain

    data = .heading.h1          # → Chain(['heading', 'h1'])
    rule = .any(0).rex(r'x\\d') # → Chain([ChainPatternAtom.any(0), ...])

    x = .x.hello.x1
    x.match(rule)               # True

    # runner.py — entry point (no sugar here)
    import latychain.ChainDotRule   # registers the hook
    import my_logic                 # gets transformed

The hook uses Python's :mod:`tokenize` module for safe, precise transformation.
It automatically skips strings, comments, object attribute access (``obj.attr``),
and float literals.

Only modules with ``# useLatyChain`` are transformed — all other imports
(stdlib, third-party libraries) pass through untouched.

.. note::
   ``.match()`` must be called on a separate Chain variable, not inside a
   chain expression — otherwise the import hook treats it as a ``ChainPatternAtom.match()``
   call, which does not exist.

   To disable the hook (e.g., in test tear-down), call
   ``latychain.ChainDotRule.unregister()``.
"""

from latychain import _hook
_hook.register()
register = _hook.register
unregister = _hook.unregister
