"""Tests for the Set class."""

from __future__ import division, print_function

import nose.tools
import itertools

from improb import Var, Point, Set, Domain

def test_set_init_1():
    a = Var('abc')
    s = Set([{a: 'a'}])
    nose.tools.assert_equal(s.domain, Domain(a))
    nose.tools.assert_equal(set(s), {Point({a: 'a'})})

def test_set_init_2():
    a = Var('abc')
    b = Var(xrange(2))
    s = Set([{a: 'a'}, {a: 'b', b: 1}])
    nose.tools.assert_equal(s.domain, Domain(a, b))
    nose.tools.assert_equal(
        set(s), {Point({a: 'a', b: 0}),
                 Point({a: 'a', b: 1}),
                 Point({a: 'b', b: 1})})

def test_set_init_3():
    a = Var('abc')
    b = Var(xrange(2))
    s = Set([{a: 'b', b: 0}, {a: 'b', b: 1}])
    nose.tools.assert_equal(s.domain, Domain(a))
    nose.tools.assert_equal(set(s), {Point({a: 'b'})})

def test_set_contains_1():
    a = Var('abc')
    s = Set([{a: 'a'}])
    nose.tools.assert_false({} in s)
    nose.tools.assert_true({a: 'a'} in s)

def test_set_contains_2():
    a = Var('abc')
    s = Set([{}])
    nose.tools.assert_true({} in s)
    nose.tools.assert_true({a: 'a'} in s)

def test_set_contains_3():
    a = Var('abc')
    b = Var(xrange(2))
    s = Set([{a: 'b', b: 0}, {a: 'b', b: 1}, {a: 'c', b: 0}])
    nose.tools.assert_true({a: 'b'} in s)
