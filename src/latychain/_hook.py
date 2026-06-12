"""Import hook: transforms .xxx.yyy.zzz() syntax into Chain([...]) calls.

Opt-in activation: only modules whose first few lines contain ``# useLatyChain``
are transformed. The hook also auto-injects ``from latychain import Chain,
ChainPatternAtom`` so you don't need to write it yourself.

Usage:
    # In the entry script (no sugar allowed here):
    import latychain.ChainDotRule
    import my_logic          # ← this gets transformed

    # In my_logic.py (first few lines must contain # useLatyChain):
    # useLatyChain
    data = .heading.h1       # -> Chain(['heading', 'h1'])
    rule = .any(0).rex(r'x\\d')  # -> Chain([ChainPatternAtom.any(0), ...])

The transformer uses Python's tokenize module to safely locate .xxx expressions
while skipping strings, comments, and attribute access (obj.attr).
"""

import io
import keyword
import logging
import os
import sys
import tokenize
import importlib.abc
import importlib.util
from typing import List, Tuple

_log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Module-level constants
# ═══════════════════════════════════════════════════════════

_LATY_MARKER = '# useLatyChain'
_AUTO_IMPORT = 'from latychain import Chain, ChainPatternAtom, Patom\n'
_WS = ' \t\n\r'
_ATOM_NAMES = frozenset({'any', 'rex', 'enum', 'apply', 'len', 'un', 'ext', 'Patom'})


def _has_laty_marker(filename: str) -> bool:
    """Check the first 10 lines of *filename* for ``# useLatyChain``.

    Only modules containing this marker **as a comment** get source-transformed.
    The marker must appear at the start of a line (ignoring leading whitespace)
    to avoid false positives inside string literals or general text.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                stripped = line.lstrip()
                if stripped.startswith(_LATY_MARKER):
                    return True
    except OSError:
        pass
    return False


# ═══════════════════════════════════════════════════════════
# Expression reader
# ═══════════════════════════════════════════════════════════

def _paren_depth(source: str, pos: int) -> int:
    r"""Consume a parenthesized block, tracking string literals.

    Returns the position of the matching closing paren.  Respects
    ``'...'``, ``"..."``, and backslash-escapes so that ``\(`` inside
    strings does not affect the depth count.
    """
    depth = 1
    quote = ''
    pos += 1
    while pos < len(source) and depth > 0:
        c = source[pos]
        if quote:
            if c == '\\' and pos + 1 < len(source):
                pos += 2  # skip escaped char (e.g. \' or \")
                continue
            if c == quote:
                quote = ''
        else:
            if c in '"\'':
                quote = c
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
        pos += 1
    return pos


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
        pos = _paren_depth(source, pos)

    # Read subsequent .xxx or .xxx() segments (skip whitespace between segments)
    # Use a lookahead approach: peek the next non-whitespace char
    while pos < len(source):
        # Remember current position in case no next segment
        saved = pos
        # Skip whitespace / newlines (will be included in expression if next segment found)
        while pos < len(source) and source[pos] in _WS:
            pos += 1
        if pos < len(source) and source[pos] == '.':
            nxt = pos + 1
            if nxt < len(source) and (source[nxt].isalnum() or source[nxt] == '_'):
                name_start = nxt
                pos = nxt
                while pos < len(source) and (source[pos].isalnum() or source[pos] == '_'):
                    pos += 1
                name = source[name_start:pos]
                # If followed by ( and name is not a known atom, stop here
                # This allows .match(data) to be a method call, not a chain segment
                if pos < len(source) and source[pos] == '(' and name not in _ATOM_NAMES:
                    pos = saved
                    break
                if pos < len(source) and source[pos] == '(':
                    pos = _paren_depth(source, pos)
                continue  # successfully read a segment, continue to look for more
        # No next segment found — restore position to before whitespace skip
        pos = saved
        break

    return source[start:pos], pos


# ═══════════════════════════════════════════════════════════
# Expression parser
# ═══════════════════════════════════════════════════════════

def _split_args(args: str) -> List[str]:
    """Split comma-separated arguments, respecting nested brackets and quotes."""
    depth = 0
    quote = ''
    current: List[str] = []
    result: List[str] = []
    i = 0
    while i < len(args):
        c = args[i]
        if quote:
            current.append(c)
            if c == '\\' and i + 1 < len(args):
                # Keep escaped char (e.g. \' inside string)
                current.append(args[i + 1])
                i += 2
                continue
            if c == quote:
                quote = ''
        elif c in '"\'':
            quote = c
            current.append(c)
        elif c in '([':
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
        i += 1
    if current:
        result.append(''.join(current).strip())
    return [r for r in result if r]


def parse_dot_expr(expr: str) -> str:
    """Parse a .xxx.yyy.zzz() expression into Chain([...]) Python code.

    Skips whitespace between segments (supports multi-line chains).
    Tracks string literals so that parentheses inside strings
    (e.g. ``.rex(r'a\\(b\\)c')``) are handled correctly.

    Example:
        ".any(0).uuu.rex(r'x\\d')"
        -> "Chain([ChainPatternAtom.any(0), 'uuu', ChainPatternAtom.rex(r'x\\d')])"
    """
    segments: List[str] = []
    pos = 0

    while pos < len(expr):
        # Skip whitespace between segments
        while pos < len(expr) and expr[pos] in _WS:
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
            _start = pos
            pos = _paren_depth(expr, pos)
            args = expr[_start + 1:pos - 1]
            transformed_args = _transform_args(args)
            segments.append(f"ChainPatternAtom.{name}({transformed_args})")
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

def _char_offset(source: str, tok) -> int:
    """Convert a token's (line, column) to a character offset in source."""
    lines = source.split('\n')
    return sum(len(l) + 1 for l in lines[:tok.start[0] - 1]) + tok.start[1]


def transform_source(source: str) -> str:
    """Transform all .xxx.yyy.zzz() expressions in source code.

    Uses tokenize to safely identify expression-context dots while
    automatically skipping strings, comments, and attribute access.
    """
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))

    # Build character-offset -> token-index lookup
    token_offsets = []
    for tok in tokens:
        off = _char_offset(source, tok)
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
            # Case 3: ).xxx(...) — transform if xxx is a ChainPatternAtom call, else skip
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

            char_offset = _char_offset(source, tok)
            try:
                expr, end_offset = read_dot_expr(source, char_offset)
            except (AssertionError, IndexError) as e:
                _log.warning(
                    "Skipping .xxx expression at line %d col %d: %s",
                    tok.start[0], tok.start[1], e,
                )
                continue

            transformed = parse_dot_expr(expr)
            replacements.append((char_offset, char_offset + len(expr), transformed))

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
        # Auto-inject the latychain imports so users don't need to write them
        transformed = _AUTO_IMPORT + transformed

        try:
            code = compile(transformed, self.origin, 'exec')
        except SyntaxError as e:
            raise ImportError(
                f"Failed to compile transformed source {self.origin}: {e}"
            ) from e
        module.__file__ = self.origin
        module.__loader__ = self
        # Set __package__ for relative imports to work inside the module
        if module.__name__ and '.' in module.__name__:
            module.__package__ = module.__name__.rsplit('.', 1)[0]
        else:
            module.__package__ = None
        exec(code, module.__dict__)


class _LatyFinder(importlib.abc.MetaPathFinder):
    """Meta path finder — only transforms modules marked with # useLatyChain."""

    def find_spec(self, fullname, path, target=None):
        for entry in (path or sys.path):
            if not entry:
                continue
            filename = os.path.join(entry, f"{fullname.replace('.', '/')}.py")
            if os.path.exists(filename) and _has_laty_marker(filename):
                return importlib.util.spec_from_loader(
                    fullname,
                    _LatyLoader(filename),
                    origin=filename,
                    is_package=False,
                )
        return None


_registered = False
_finder = None


def register():
    """Install the import hook. Called automatically by ``import latychain.ChainDotRule``."""
    global _registered, _finder
    if not _registered:
        _finder = _LatyFinder()
        sys.meta_path.insert(0, _finder)
        _registered = True


def unregister():
    """Remove the import hook from ``sys.meta_path``.

    Useful in test suites or interactive environments where you want to
    disable the ``.xxx.yyy`` transformation. Safe to call even if the hook
    was never registered.
    """
    global _registered, _finder
    if _registered and _finder is not None:
        try:
            sys.meta_path.remove(_finder)
        except ValueError:
            pass
        _finder = None
        _registered = False
