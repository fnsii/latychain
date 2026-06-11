"""Run all latychain tests — both core API and import-hook sugar syntax."""

import sys
import os

_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
_test = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _src)
sys.path.insert(0, _test)

print('=' * 55)
print('Part 1: Core API  (Chain / ChainRuleAtom, no sugar)')
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
print('All tests completed.')
print('=' * 55)
