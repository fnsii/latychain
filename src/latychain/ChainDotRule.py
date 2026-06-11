"""Import hook to enable ``.xxx.yyy`` syntax sugar.

Once imported, all subsequently loaded Python modules have their
``.xxx.yyy.zzz()`` expressions automatically transformed into
``Chain([...])`` calls at compile time.

Usage::

    import latychain.ChainDotRule
    from latychain import Chain

    # Data chain — segments without () become strings
    data = .heading.h1          # → Chain(['heading', 'h1'])

    # Rule chain — segments with () become ChainRuleAtom.xxx() calls
    rule = .any(0).rex(r'x\\d') # → Chain([ChainRuleAtom.any(0), ChainRuleAtom.rex(...)])

    # Matching
    .x.hello.x1.match(rule)     # True

The hook uses Python's :mod:`tokenize` module for safe, precise transformation.
It automatically skips strings, comments, object attribute access (``obj.attr``),
and float literals.

Only needs to be imported once at the entry point. All modules imported
*after* this one will be transformed.
"""

from latychain import _hook
_hook.register()
