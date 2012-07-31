"""Extra tests for Set hash implementation."""

from __future__ import division, print_function

import nose.tools

from improb import Var, Func, Set

def test_hash_1():
    a1 = Var('abc')
    a2 = Var([1, 2])
    pts1 = Set([
        {a1: 'a'},
        {a1: 'b'},
        {a1: 'c'},
        ])
    pts2 = Set([
        {a2: 1},
        {a2: 2},
        ])
    nose.tools.assert_equal(hash(pts1), hash(pts2))

def test_hash_2():
    a1 = Var('abc')
    a2 = Var([1, 2])
    pts1 = Set([
        {a1: 'a', a2: 1},
        {a1: 'a', a2: 2},
        ])
    pts2 = Set([
        {a1: 'a'},
        ])
    nose.tools.assert_equal(hash(pts1), hash(pts2))

def test_hash_3():
    a1 = Var('abc')
    a2 = Var([1, 2])
    a3 = Var('ab')
    pts1 = Set([
        {a1: 'a', a2: 1},
        {a1: 'a', a2: 2},
        ])
    pts2 = Set([
        {a3: 'a'},
        ])
    nose.tools.assert_not_equal(hash(pts1), hash(pts2))

def test_hash_4():
    a1 = Var('abc')
    a2 = Var([1, 2])
    pts1 = Set([
        {a1: 'a', a2: 1},
        {a1: 'b', a2: 2},
        ])
    pts2 = Set([
        {a1: 'a', a2: 2},
        {a1: 'b', a2: 1},
        ])
    nose.tools.assert_not_equal(hash(pts1), hash(pts2))

def test_hash_5():
    a1 = Var('abc')
    a2 = Var([1, 2])
    a3 = Var('xy')
    pts1 = Set([
        {a1: 'a', a2: 1, a3: 'x'},
        {a1: 'a', a2: 2, a3: 'x'},
        {a1: 'a', a2: 1, a3: 'y'},
        {a1: 'a', a2: 2, a3: 'y'},
        ])
    pts2 = Set([
        {a1: 'a', a2: 1},
        {a1: 'a', a2: 2},
        ])
    pts3 = Set([
        {a1: 'a', a3: 'x'},
        {a1: 'a', a3: 'y'},
        ])
    pts4 = Set([
        {a1: 'a'},
        ])
    nose.tools.assert_equal(hash(pts1), hash(pts2))
    nose.tools.assert_equal(hash(pts1), hash(pts3))
    nose.tools.assert_equal(hash(pts1), hash(pts4))

def test_hash_func_1():
    a1 = Var('abc')
    a2 = Var([1, 2])
    f1 = Func(a1, [0, 1, 2])
    f2 = Func([a1, a2], [0, 0, 1, 1, 2, 2])
    nose.tools.assert_equal(hash(f1), hash(f2))

def test_hash_func_2():
    a1 = Var('abc')
    a2 = Var([1, 2])
    f1 = Func(a1, [0, 1, 2])
    f2 = Func([a1, a2], [0, 1, 1, 0, 2, 2])
    nose.tools.assert_not_equal(hash(f1), hash(f2))
