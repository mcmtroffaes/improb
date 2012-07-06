"""Tests for events."""

# events are variables which take the values True and False
# here we check that all operations for these work as expected


from __future__ import division, print_function

import nose.tools
import itertools

from improb import Domain, Var, Func

def test_event_not():
    a = Var('abc')
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    b = Func(a, [False, True, False])
    c = b.not_()
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [True, False, True])

def test_func_not():
    a = Var('abc')
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    b = Func(a, [0, 1, 1])
    c = b.not_()
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [True, False, False])

def test_event_and_or_xor():
    a = Var('abcd')
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}, {a: 'd'}]
    b = Func(a, [False, True, False, True])
    c = Func(a, [True, True, False, False])
    d = b & c
    nose.tools.assert_sequence_equal(
        [d.get_value(w) for w in points], [False, True, False, False])
    d = b | c
    nose.tools.assert_sequence_equal(
        [d.get_value(w) for w in points], [True, True, False, True])
    d = b ^ c
    nose.tools.assert_sequence_equal(
        [d.get_value(w) for w in points], [True, False, False, True])
