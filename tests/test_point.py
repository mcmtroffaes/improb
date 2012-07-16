"""Tests for the Point class."""

from __future__ import division, print_function

import nose.tools
import itertools

from improb import Var, Point

def test_point_init_get_1():
    a = Var('abc')
    p = Point({a: 'a'})
    nose.tools.assert_equal(p[a], 'a')

def test_point_init_2():
    a = Var('abc')
    nose.tools.assert_raises(ValueError, lambda: Point({a: 'd'}))

@nose.tools.raises(TypeError)
def test_point_init_3():
    p = Point({'a': 'a'})

@nose.tools.raises(TypeError)
def test_point_init_4():
    p = Point('a')

def test_point_init_5():
    p = Point({})

def test_point_len_1():
    p = Point({})
    nose.tools.assert_equal(len(p), 0)
    nose.tools.assert_false(p)

def test_point_len_2():
    a = Var('abc')
    p = Point({a: 'a'})
    nose.tools.assert_equal(len(p), 1)
    nose.tools.assert_true(p)

def test_point_len_3():
    a = Var('abc')
    b = Var(xrange(2))
    p = Point({a: 'a', b: 1})
    nose.tools.assert_equal(len(p), 2)
    nose.tools.assert_true(p)

def test_point_get_1():
    a = Var('abc')
    b = Var(xrange(5))
    c = Var('*+-/')
    p = Point({a: 'c', b: 2})
    nose.tools.assert_equal(p[a], 'c')
    nose.tools.assert_equal(p[b], 2)
    nose.tools.assert_raises(KeyError, lambda: p[c])

def test_point_eq_1():
    a = Var('abc')
    b = Var(xrange(5))
    p = Point({a: 'c', b: 2})
    nose.tools.assert_equal(p, {a: 'c', b: 2})

def test_point_iter_1():
    a = Var('abc')
    b = Var(xrange(5))
    p = Point({a: 'c', b: 2})
    nose.tools.assert_equal(set(p), {a, b})
    nose.tools.assert_equal(set(p.itervalues()), {'c', 2})

def test_point_str_repr():
    a = Var('abc', name='X1')
    b = Var(xrange(5), name='X2')
    p = Point({a: 'c', b: 2})
    nose.tools.assert_equal(str(p), "X1=c & X2=2")
    nose.tools.assert_equal(repr(p), "Point({Var(['a', 'b', 'c'], name='X1'): 'c', Var([0, 1, 2, 3, 4], name='X2'): 2})")
