"""Run all latychain tests — core API, import-hook sugar, doc examples, and README verification."""

import sys
import os

_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
_test = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _src)
sys.path.insert(0, _test)

print('=' * 55)
print('Part 1: Core API  (Chain / ChainPatternAtom, no sugar)')
print('=' * 55)

import test_core

print()

print('=' * 55)
print('Part 2: Sugar syntax  (.xxx.yyy via import hook)')
print('=' * 55)

import latychain.ChainDotRule
import _test_sugar

print()

print('=' * 55)
print('Part 3: Doc examples (explicit API)')
print('=' * 55)

import _test_doc_examples

print()

print('=' * 55)
print('Part 4: Doc examples (sugar syntax via hook)')
print('=' * 55)

import _test_doc_sugar

print()

print('=' * 55)
print('Part 5: README explicit snippets verification')
print('=' * 55)

import _verify_readme_explicit

_count = 0
_fail = 0
for fn in _verify_readme_explicit.ALL_TESTS:
    try:
        fn()
        _count += 1
    except AssertionError as e:
        print(f'  FAIL {fn.__name__}: {e}')
        _fail += 1
    except Exception as e:
        print(f'  ERROR {fn.__name__}: {type(e).__name__}: {e}')
        _fail += 1
print(f'README explicit snippets: {_count} passed, {_fail} failed')

print()

print('=' * 55)
print('Part 6: README sugar snippets verification')
print('=' * 55)

import _verify_readme_sugar

print()

print('=' * 55)
print('All tests completed.')
print('=' * 55)
