# -*- coding: utf-8 -*-
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

def test_set_and_1():
    a = Var('abc')
    s1 = Set([{}])
    s2 = Set([{a: 'b'}, {a: 'c'}])
    nose.tools.assert_equal(s1 & s2, s2)

def test_set_and_2():
    a = Var('abc')
    s1 = Set([])
    s2 = Set([{a: 'b'}, {a: 'c'}])
    nose.tools.assert_equal(s1 & s2, s1)

def test_set_and_3():
    a = Var('abc')
    b = Var(xrange(2))
    s1 = Set([{a: 'a'}])
    s2 = Set([{b: 0}])
    s3 = Set([{a: 'a', b: 0}])
    nose.tools.assert_equal(s1 & s2, s3)

def test_set_or_1():
    a = Var('abc')
    s1 = Set([{}])
    s2 = Set([{a: 'b'}, {a: 'c'}])
    nose.tools.assert_equal(s1 | s2, s1)

def test_set_or_2():
    a = Var('abc')
    s1 = Set([])
    s2 = Set([{a: 'b'}, {a: 'c'}])
    nose.tools.assert_equal(s1 | s2, s2)

def test_set_or_3():
    a = Var('abc')
    b = Var(xrange(3))
    s1 = Set([{a: 'a'}])
    s2 = Set([{b: 0}])
    s3 = Set([{a: 'a', b: 0}, {a: 'a', b: 1}, {a: 'a', b: 2},
              {a: 'a', b: 0}, {a: 'b', b: 0}, {a: 'c', b: 0},
              ])
    nose.tools.assert_equal(s1 | s2, s3)

def test_set_sub_1():
    a = Var('abc')
    s1 = Set([{}])
    s2 = Set([{a: 'a'}])
    s3 = Set([{a: 'b'}, {a: 'c'}])
    nose.tools.assert_equal(s1 - s2, s3)
    nose.tools.assert_equal(s2 - s1, Set([]))

def test_set_sub_2():
    a = Var('abc')
    s1 = Set([])
    s2 = Set([{a: 'a'}])
    nose.tools.assert_equal(s1 - s2, s1)
    nose.tools.assert_equal(s2 - s1, s2)

def test_set_sub_3():
    a = Var('abc')
    b = Var(xrange(2))
    s1 = Set([{a: 'a'}])
    s2 = Set([{b: 0}])
    s3 = Set([{a: 'a', b: 1}])
    s4 = Set([{a: 'b', b: 0}, {a: 'c', b: 0}])
    nose.tools.assert_equal(s1 - s2, s3)
    nose.tools.assert_equal(s2 - s1, s4)

def test_set_le_1():
    a = Var('abc')
    dom = Domain(a)
    event = Set([{}])
    contains = Set([{a: 'a'}, {a: 'b'}])
    nose.tools.assert_true(contains <= event)

def test_set_str_repr_0():
    s = Set([])
    nose.tools.assert_equal(str(s), "∅")
    nose.tools.assert_equal(repr(s), "Set([])")

def test_set_str_repr_1():
    s = Set([{}])
    nose.tools.assert_equal(str(s), "Ω")
    nose.tools.assert_equal(repr(s), "Set([{}])")

def test_set_str_repr_2():
    a = Var('abc', name="X1")
    b = Var(xrange(2), name="X2")
    s = Set([{a: 'a'}, {a: 'b', b: 1}])
    nose.tools.assert_equal(
        str(s), "(X1=a & X2=0) | (X1=a & X2=1) | (X1=b & X2=1)")
    nose.tools.assert_equal(
        repr(s),
        "Set(["
        "{Var(['a', 'b', 'c'], name='X1'): 'a', Var([0, 1], name='X2'): 0}, "
        "{Var(['a', 'b', 'c'], name='X1'): 'a', Var([0, 1], name='X2'): 1}, "
        "{Var(['a', 'b', 'c'], name='X1'): 'b', Var([0, 1], name='X2'): 1}"
        "])")
