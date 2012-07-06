"""Tests for the Var class."""

from __future__ import division, print_function

import nose.tools
import itertools

from improb import Domain, Var

def test_var_add_scalar():
    a = Var(xrange(3))
    points = list(a.domain.points())
    b = 2 + a
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [2, 3, 4])
    c = a + 2
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [2, 3, 4])
    nose.tools.assert_equal(b, c)

def test_var_sub_scalar():
    a = Var(xrange(3))
    points = list(a.domain.points())
    b = 2 - a
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [2, 1, 0])
    c = a - 2
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [-2, -1, 0])

def test_var_mul_scalar():
    a = Var(xrange(3))
    points = list(a.domain.points())
    b = 2 * a
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [0, 2, 4])
    c = a * 2
    nose.tools.assert_sequence_equal(
        [c.get_value(w) for w in points], [0, 2, 4])
    nose.tools.assert_equal(b, c)

def test_var_truediv_scalar():
    a = Var(xrange(3))
    points = list(a.domain.points())
    b = a / 2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [0.0, 0.5, 1.0])

def test_var_floordiv_scalar():
    a = Var(xrange(3))
    points = list(a.domain.points())
    b = a // 2
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [0, 0, 1])

def test_var_add_var():
    a1 = Var(xrange(3))
    a2 = Var(xrange(5, 15, 3))
    b = a1 + a2
    points = list(b.domain.points())
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [5, 8, 11, 14, 6, 9, 12, 15, 7, 10, 13, 16])

def test_var_sub_var():
    a1 = Var(xrange(3))
    a2 = Var(xrange(5, 15, 3))
    b = a1 - a2
    points = list(b.domain.points())
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [-5, -8, -11, -14, -4, -7, -10, -13, -3, -6, -9, -12])

def test_var_mul_var():
    a1 = Var(xrange(3))
    a2 = Var(xrange(5, 15, 3))
    b = a1 * a2
    points = list(b.domain.points())
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points],
        [0, 0, 0, 0, 5, 8, 11, 14, 10, 16, 22, 28])

def test_var_neg():
    a = Var(xrange(3))
    points = list(a.domain.points())
    b = -a
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [0, -1, -2])

def test_var_eq():
    a = Var('abcde')
    points = list(a.domain.points())
    b = a.eq_('d')
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [False, False, False, True, False])

def test_var_ne():
    a = Var('abcde')
    points = list(a.domain.points())
    b = a.ne_('b')
    nose.tools.assert_sequence_equal(
        [b.get_value(w) for w in points], [True, False, True, True, True])

def test_var_min_max():
    a = Var(xrange(5, 21, 3))
    nose.tools.assert_equal(a.minimum(), 5)
    nose.tools.assert_equal(a.maximum(), 20)
