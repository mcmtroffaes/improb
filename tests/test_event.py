"""Tests for events."""

# events are variables which take the values True and False
# here we check that all operations for these work as expected


from __future__ import division, print_function

import nose.tools
import itertools

from improb import Domain, Var, Func, Point

def test_event_not():
    a = Var('abc')
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    b = Func(a, {'a': False, 'b': True, 'c': False})
    c = b.not_()
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [True, False, True])

def test_func_not():
    a = Var('abc')
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    b = Func(a, {'a': 0, 'b': 1, 'c': 1})
    c = b.not_()
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [True, False, False])

def test_event_and_or_xor():
    a = Var('abcd')
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}, {a: 'd'}]
    b = Func(a, lambda av: av in 'bd')
    c = Func(a, lambda av: av in 'ab')
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
    b = Func(a, lambda av: av in 'bd')
    nose.tools.assert_set_equal(
        set(b.points()), set([Point({a: 'b'}), Point({a: 'd'})]))

def test_event_equality_1():
    a1 = Var('abcd', name='a1')
    a2 = Var('abcd', name='a2')
    nose.tools.assert_false(a1.is_equivalent_to(a2))
    nose.tools.assert_not_equal(a1, a2)

def test_event_equality_2():
    a1 = Var('abcd')
    a2 = Var('gh')
    b = Func(a1, lambda a1v: a1v in 'bd')
    c = Func([a1, a2], {
        ('a', 'g'): 0,
        ('a', 'h'): 2,
        ('b', 'g'): 1,
        ('b', 'h'): 1,
        ('c', 'g'): 2,
        ('c', 'h'): 0,
        ('d', 'g'): 1,
        ('d', 'h'): 1,
        })
    d = Func(c, {0: False, 2: False, 1: True})
    nose.tools.assert_true(b.is_equivalent_to(d))
    nose.tools.assert_true(b.eq_(d).all())
    nose.tools.assert_equal(b, d)
    nose.tools.assert_equal(set(b.eq_(d).itervalues()), set([True]))
