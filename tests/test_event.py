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

def test_event_points():
    a = Var('abcd')
    b = Func(a, [False, True, False, True])
    nose.tools.assert_sequence_equal(
        list(b.points()), [{a: 'b'}, {a: 'd'}])

def test_event_equality_1():
    a1 = Var('abcd', name='a1')
    a2 = Var('abcd', name='a2')
    nose.tools.assert_false(a1.is_equivalent_to(a2))
    nose.tools.assert_not_equal(a1, a2)

def test_event_equality_2():
    a1 = Var('abcd')
    a2 = Var('gh')
    b = Func(a1, [False, True, False, True])
    c = Func([a1, a2], [0, 2, 1, 1, 2, 0, 1, 1])
    d = Func(c, {0: False, 2: False, 1: True})
    nose.tools.assert_true(b.is_equivalent_to(d))
    nose.tools.assert_true(b.eq_(d).all())
    nose.tools.assert_equal(b, d)
    nose.tools.assert_equal(set(b.eq_(d).itervalues()), set([True]))
