"""Import hook: transforms .xxx.yyy.zzz() syntax into Chain([...]) calls.

Usage:
    import LatyChain.ChainDotRule   # auto-registers the hook
    from latychain import Chain

    data = .heading.h1            # -> Chain(['heading', 'h1'])
    rule = .any(0).rex(r'x\\d')   # -> Chain([ChainRuleAtom.any(0), ChainRuleAtom.rex(...)])

The transformer uses Python's tokenize module to safely locate .xxx expressions
while skipping strings, comments, and attribute access (obj.attr).
"""

import io
import keyword
import os
import sys
import tokenize
import importlib.abc
import importlib.util
from typing import List, Tuple


# ═══════════════════════════════════════════════════════════
# Expression reader
# ═══════════════════════════════════════════════════════════

def read_dot_expr(source: str, pos: int) -> Tuple[str, int]:
    """Read a complete .xxx.yyy.zzz() expression from source at pos.

    Handles arbitrarily nested parentheses in arguments and skips
    whitespace/newlines between segments (supports multi-line chains).

    Args:
        source: The full source code string.
        pos: Byte offset where the expression starts (the '.' character).

    Returns:
        (expression_string, end_offset)
    """
    start = pos
    assert source[pos] == '.', f"Expected '.' at offset {pos}, got {source[pos]!r}"
    pos += 1

    # Read segment name
    while pos < len(source) and (source[pos].isalnum() or source[pos] == '_'):
        pos += 1

    # Read optional (args) with stack-based parenthesis matching
    if pos < len(source) and source[pos] == '(':
        depth = 1
        pos += 1
        while pos < len(source) and depth > 0:
            if source[pos] == '(':
                depth += 1
            elif source[pos] == ')':
                depth -= 1
            pos += 1

    # Read subsequent .xxx or .xxx() segments (skip whitespace between segments)
    # Use a lookahead approach: peek the next non-whitespace char
    _ws = ' \t\n\r'
    while pos < len(source):
        # Remember current position in case no next segment
        saved = pos
        # Skip whitespace / newlines (will be included in expression if next segment found)
        while pos < len(source) and source[pos] in _ws:
            pos += 1
        if pos < len(source) and source[pos] == '.':
            nxt = pos + 1
            if nxt < len(source) and source[nxt].isalpha():
                pos = nxt
                while pos < len(source) and (source[pos].isalnum() or source[pos] == '_'):
                    pos += 1
                if pos < len(source) and source[pos] == '(':
                    depth = 1
                    pos += 1
                    while pos < len(source) and depth > 0:
                        if source[pos] == '(':
                            depth += 1
                        elif source[pos] == ')':
                            depth -= 1
                        pos += 1
                continue  # successfully read a segment, continue to look for more
        # No next segment found — restore position to before whitespace skip
        pos = saved
        break

    return source[start:pos], pos


# ═══════════════════════════════════════════════════════════
# Expression parser
# ═══════════════════════════════════════════════════════════

def _split_args(args: str) -> List[str]:
    """Split comma-separated arguments, respecting nested brackets."""
    depth = 0
    current: List[str] = []
    result: List[str] = []
    for c in args:
        if c in '([':
            depth += 1
            current.append(c)
        elif c in ')]':
            depth -= 1
            current.append(c)
        elif c == ',' and depth == 0:
            result.append(''.join(current).strip())
            current = []
        else:
            current.append(c)
    if current:
        result.append(''.join(current).strip())
    return [r for r in result if r]


def parse_dot_expr(expr: str) -> str:
    """Parse a .xxx.yyy.zzz() expression into Chain([...]) Python code.

    Skips whitespace between segments (supports multi-line chains).

    Example:
        ".any(0).uuu.rex(r'x\\d')"
        -> "Chain([ChainRuleAtom.any(0), 'uuu', ChainRuleAtom.rex(r'x\\d')])"
    """
    segments: List[str] = []
    pos = 0

    while pos < len(expr):
        # Skip whitespace between segments
        while pos < len(expr) and expr[pos] in ' \t\n\r':
            pos += 1
        if pos >= len(expr):
            break
        assert expr[pos] == '.', f"Expected '.' at offset {pos}"
        pos += 1

        name_start = pos
        while pos < len(expr) and (expr[pos].isalnum() or expr[pos] == '_'):
            pos += 1
        name = expr[name_start:pos]
        if not name:
            raise SyntaxError(f"Empty segment name in expression: {expr}")

        if pos < len(expr) and expr[pos] == '(':
            args_start = pos + 1
            depth = 1
            pos += 1
            while pos < len(expr) and depth > 0:
                if expr[pos] == '(':
                    depth += 1
                elif expr[pos] == ')':
                    depth -= 1
                pos += 1
            args = expr[args_start:pos - 1]
            transformed_args = _transform_args(args)
            segments.append(f"ChainRuleAtom.{name}({transformed_args})")
        else:
            segments.append(repr(name))

    return f"Chain([{', '.join(segments)}])"


def _transform_args(args: str) -> str:
    """Recursively transform .xxx expressions inside function arguments."""
    parts = []
    for arg in _split_args(args):
        arg = arg.strip()
        if arg.startswith('.'):
            parts.append(parse_dot_expr(arg))
        else:
            parts.append(arg)
    return ', '.join(parts)


# ═══════════════════════════════════════════════════════════
# Source transformer (tokenize-based)
# ═══════════════════════════════════════════════════════════

def _token_offset(source: str, tok) -> int:
    """Convert a token's (line, column) to a byte offset in source."""
    lines = source.split('\n')
    return sum(len(l) + 1 for l in lines[:tok.start[0] - 1]) + tok.start[1]


def transform_source(source: str) -> str:
    """Transform all .xxx.yyy.zzz() expressions in source code.

    Uses tokenize to safely identify expression-context dots while
    automatically skipping strings, comments, and attribute access.
    """
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))

    # Build byte-offset -> token-index lookup
    token_offsets = []
    for tok in tokens:
        off = _token_offset(source, tok)
        token_offsets.append(off)

    replacements: List[Tuple[int, int, str]] = []
    skip_until_token = -1  # skip tokens inside already-matched expressions

    for i, tok in enumerate(tokens):
        if i <= skip_until_token:
            continue

        if tok.type in (tokenize.STRING, tokenize.COMMENT):
            continue

        if (tok.type == tokenize.OP
                and tok.string == '.'
                and i + 1 < len(tokens)
                and tokens[i + 1].type == tokenize.NAME
                and tokens[i + 1].string[0].isalpha()):

            # --- Determine whether to skip ---
            # Case 1: obj.attr, print.attr, etc. — skip
            # Case 2: assert .xxx, return .xxx — transform (keyword before dot)
            # Case 3: ).xxx(...) — transform if xxx is a ChainRuleAtom call, else skip
            # Case 4: 123.attr, ].attr, }.attr — skip
            if i > 0:
                prev = tokens[i - 1]

                if prev.type == tokenize.NUMBER:
                    continue  # 123.attr → skip

                if prev.type == tokenize.OP and prev.string in ']}':
                    continue  # ].attr, }.attr → skip

                if prev.type == tokenize.OP and prev.string == ')':
                    # ).xxx — could be func().attr (skip) or ).rex(...) (transform)
                    # Only transform known atom calls after )
                    _ATOM_NAMES = frozenset({'any', 'rex', 'enum', 'apply', 'long', 'un', 'ext'})
                    is_atom_call = (
                        i + 2 < len(tokens)
                        and tokens[i + 1].type == tokenize.NAME
                        and tokens[i + 1].string in _ATOM_NAMES
                        and tokens[i + 2].type == tokenize.OP
                        and tokens[i + 2].string == '('
                    )
                    if not is_atom_call:
                        continue  # func().attr or func().method() → skip

                if prev.type == tokenize.NAME and prev.string not in keyword.kwlist:
                    continue  # obj.attr → skip; assert .xxx → transform

            byte_offset = _token_offset(source, tok)
            try:
                expr, end_offset = read_dot_expr(source, byte_offset)
            except AssertionError:
                continue

            transformed = parse_dot_expr(expr)
            replacements.append((byte_offset, byte_offset + len(expr), transformed))

            # Skip all tokens whose byte offset falls inside this expression
            for j in range(i + 1, len(tokens)):
                if token_offsets[j] >= end_offset:
                    skip_until_token = j - 1
                    break
            else:
                skip_until_token = len(tokens) - 1

    # Apply right-to-left to preserve offsets
    replacements.sort(key=lambda x: x[0], reverse=True)
    result = list(source)
    for start, end, text in replacements:
        result[start:end] = text
    return ''.join(result)


# ═══════════════════════════════════════════════════════════
# Import hook
# ═══════════════════════════════════════════════════════════

class _LatyLoader(importlib.abc.Loader):
    """Custom loader that transforms source before compilation."""

    def __init__(self, origin: str):
        self.origin = origin

    def exec_module(self, module):
        with open(self.origin, 'r', encoding='utf-8') as f:
            source = f.read()
        try:
            transformed = transform_source(source)
        except SyntaxError as e:
            raise ImportError(
                f"Failed to transform {self.origin}: {e}"
            ) from e

        code = compile(transformed, self.origin, 'exec')
        module.__file__ = self.origin
        module.__loader__ = self
        exec(code, module.__dict__)


class _LatyFinder(importlib.abc.MetaPathFinder):
    """Meta path finder that intercepts all .py imports for transformation."""

    def find_spec(self, fullname, path, target=None):
        for entry in (path or sys.path):
            if not entry:
                continue
            filename = os.path.join(entry, f"{fullname.replace('.', '/')}.py")
            if os.path.exists(filename):
                return importlib.util.spec_from_loader(
                    fullname,
                    _LatyLoader(filename),
                    origin=filename,
                    is_package=False,
                )
        return None


_registered = False


def register():
    """Install the import hook. Called automatically by LatyChain.ChainDotRule."""
    global _registered
    if not _registered:
        sys.meta_path.insert(0, _LatyFinder())
        _registered = True
