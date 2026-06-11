"""latychain — chain-structured data and pattern matching.

Provides Chain (immutable ordered container) and ChainRuleAtom (rule atoms).
Use LatyChain.ChainDotRule to enable .xxx.yyy syntax sugar.
"""

from latychain._chain import Chain
from latychain._atoms import ChainRuleAtom

__all__ = [
    "Chain",
    "ChainRuleAtom",
]
