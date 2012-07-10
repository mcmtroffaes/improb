"""Tests for the Func class."""

from __future__ import division, print_function

import nose.tools
import itertools

from improb import Domain, Var, Func

def test_func_init_from_dict_1():
    a = Var('abc')
    b = Func(a, {'a': 0, 'b': 2, 'c': 6})
    nose.tools.assert_equal(b.get_value({a: 'a'}), 0)
    nose.tools.assert_equal(b.get_value({a: 'b'}), 2)
    nose.tools.assert_equal(b.get_value({a: 'c'}), 6)

def test_func_init_from_dict_2():
    a1 = Var('abc')
    a2 = Var(xrange(3))
    b = Func([a1, a2], {
        ('a', 0): 3,
        ('a', 1): 5,
        ('a', 2): 2,
        ('b', 0): 8,
        ('b', 1): 2,
        ('b', 2): 1,
        ('c', 0): 6,
        ('c', 1): 7,
        ('c', 2): 4,
        })
    nose.tools.assert_equal(b.get_value({a1: 'a', a2: 0}), 3)
    nose.tools.assert_equal(b.get_value({a1: 'a', a2: 1}), 5)
    nose.tools.assert_equal(b.get_value({a1: 'a', a2: 2}), 2)
    nose.tools.assert_equal(b.get_value({a1: 'b', a2: 0}), 8)
    nose.tools.assert_equal(b.get_value({a1: 'b', a2: 1}), 2)
    nose.tools.assert_equal(b.get_value({a1: 'b', a2: 2}), 1)
    nose.tools.assert_equal(b.get_value({a1: 'c', a2: 0}), 6)
    nose.tools.assert_equal(b.get_value({a1: 'c', a2: 1}), 7)
    nose.tools.assert_equal(b.get_value({a1: 'c', a2: 2}), 4)

def test_func_values_1():
    a1 = Var('ab')
    a2 = Var(xrange(2))
    b = Func([a1, a2], {
        ('a', 0): 3,
        ('a', 1): 5,
        ('b', 0): 8,
        ('b', 1): 2,
        ('c', 0): 100,
        ('c', 1): 110,
        })
    nose.tools.assert_equal(set(b.itervalues()), set([2, 3, 5, 8]))

def test_func_init_from_list_1():
    a = Var('abc')
    b = Func(a, [0, 2, 6])
    nose.tools.assert_equal(b.get_value({a: 'a'}), 0)
    nose.tools.assert_equal(b.get_value({a: 'b'}), 2)
    nose.tools.assert_equal(b.get_value({a: 'c'}), 6)

def test_func_init_from_list_2():
    a1 = Var('abc')
    a2 = Var(xrange(3))
    b = Func([a1, a2], [3, 5, 2, 8, 2, 1, 6, 7, 4])
    nose.tools.assert_equal(b.get_value({a1: 'a', a2: 0}), 3)
    nose.tools.assert_equal(b.get_value({a1: 'a', a2: 1}), 5)
    nose.tools.assert_equal(b.get_value({a1: 'a', a2: 2}), 2)
    nose.tools.assert_equal(b.get_value({a1: 'b', a2: 0}), 8)
    nose.tools.assert_equal(b.get_value({a1: 'b', a2: 1}), 2)
    nose.tools.assert_equal(b.get_value({a1: 'b', a2: 2}), 1)
    nose.tools.assert_equal(b.get_value({a1: 'c', a2: 0}), 6)
    nose.tools.assert_equal(b.get_value({a1: 'c', a2: 1}), 7)
    nose.tools.assert_equal(b.get_value({a1: 'c', a2: 2}), 4)

def test_func_add_scalar():
    a = Var('abc')
    b = Func(a, [0, 1, 2])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    c = 2 + b
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [2, 3, 4])
    d = b + 2
    nose.tools.assert_sequence_equal(
        [d.get_value(w) for w in points], [2, 3, 4])
    nose.tools.assert_equal(c, d)

def test_func_sub_scalar():
    a = Var('abc')
    b = Func(a, [0, 1, 2])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    c = 2 - b
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [2, 1, 0])
    d = b - 2
    nose.tools.assert_sequence_equal(
        [d.get_value(w) for w in points], [-2, -1, 0])

def test_func_mul_scalar():
    a = Var('abc')
    b = Func(a, [0, 1, 2])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    c = 2 * b
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [0, 2, 4])
    d = b * 2
    nose.tools.assert_sequence_equal(
        [d.get_value(w) for w in points], [0, 2, 4])
    nose.tools.assert_equal(c, d)

def test_func_truediv_scalar():
    a = Var('abc')
    b = Func(a, [0, 1, 2])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    c = b / 2
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [0.0, 0.5, 1.0])

def test_func_floordiv_scalar():
    a = Var('abc')
    b = Func(a, [0, 1, 2])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    c = b // 2
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [0, 0, 1])

def test_func_add_func():
    a1 = Var(xrange(3))
    a2 = Var('ab')
    b1 = Func([a1, a2], [1, 3, 4, 2, -1, 3])
    b2 = Func(a2, [0, 6])
    points = [
        {a1: 0, a2: 'a'}, {a1: 0, a2: 'b'},
        {a1: 1, a2: 'a'}, {a1: 1, a2: 'b'},
        {a1: 2, a2: 'a'}, {a1: 2, a2: 'b'},
        ]
    b = b1 + b2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [1, 9, 4, 8, -1, 9])
    b = b1 + a1
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [1, 3, 5, 3, 1, 5])
    b = a1 + b2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [0, 6, 1, 7, 2, 8])

def test_func_sub_func():
    a1 = Var(xrange(3))
    a2 = Var('ab')
    b1 = Func([a1, a2], [1, 3, 4, 2, -1, 3])
    b2 = Func(a2, [0, 6])
    points = [
        {a1: 0, a2: 'a'}, {a1: 0, a2: 'b'},
        {a1: 1, a2: 'a'}, {a1: 1, a2: 'b'},
        {a1: 2, a2: 'a'}, {a1: 2, a2: 'b'},
        ]
    b = b1 - b2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [1, -3, 4, -4, -1, -3])
    b = b1 - a1
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [1, 3, 3, 1, -3, 1])
    b = a1 - b2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [0, -6, 1, -5, 2, -4])

def test_func_mul_func():
    a1 = Var(xrange(3))
    a2 = Var('ab')
    b1 = Func([a1, a2], [1, 3, 4, 2, -1, 3])
    b2 = Func(a2, [0, 6])
    points = [
        {a1: 0, a2: 'a'}, {a1: 0, a2: 'b'},
        {a1: 1, a2: 'a'}, {a1: 1, a2: 'b'},
        {a1: 2, a2: 'a'}, {a1: 2, a2: 'b'},
        ]
    b = b1 * b2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [0, 18, 0, 12, 0, 18])
    b = b1 * a1
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [0, 0, 4, 2, -2, 6])
    b = a1 * b2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [0, 0, 0, 6, 0, 12])

def test_func_neg():
    a = Var('abc')
    b = Func(a, [0, 1, 2])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}]
    c = -b
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [0, -1, -2])

def test_func_eq():
    a = Var('abcde')
    b = Func(a, [0, 1, 2, 2, 1])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}, {a: 'd'}, {a: 'e'}]
    c = b.eq_(1)
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [False, True, False, False, True])

def test_func_ne():
    a = Var('abcde')
    b = Func(a, [0, 1, 2, 2, 1])
    points = [{a: 'a'}, {a: 'b'}, {a: 'c'}, {a: 'd'}, {a: 'e'}]
    c = b.ne_(2)
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [True, True, False, False, True])

def test_func_min_max():
    a = Var('abcde')
    b = Func(a, [5, 2, 3, 8, 4])
    nose.tools.assert_equal(b.minimum(), 2)
    nose.tools.assert_equal(b.maximum(), 8)
