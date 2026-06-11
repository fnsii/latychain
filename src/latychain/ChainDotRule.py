"""ChainDotRule — import to enable .xxx.yyy syntax.

Once imported, all subsequently loaded modules have their
.xxx.yyy.zzz() expressions transformed into Chain([...]) calls.

Example::

    import latychain.ChainDotRule
    from latychain import Chain

    data = .heading.h1          # -> Chain(['heading', 'h1'])
    rule = .any(0).rex(r'x\\d') # -> Chain([ChainRuleAtom.any(0), ChainRuleAtom.rex(...)])
"""

from latychain import _hook
_hook.register()
