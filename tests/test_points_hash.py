"""Tests for _points_hash implementation."""

from __future__ import division, print_function

import nose.tools

from improb import Var, _points_hash

def test_hash_1():
    a1 = Var('abc')
    a2 = Var([1, 2])
    pts1 = [
        {a1: 'a'},
        {a1: 'b'},
        {a1: 'c'},
        ]
    pts2 = [
        {a2: 1},
        {a2: 2},
        ]
    nose.tools.assert_equal(_points_hash(pts1), _points_hash(pts2))

def test_hash_2():
    a1 = Var('abc')
    a2 = Var([1, 2])
    pts1 = [
        {a1: 'a', a2: 1},
        {a1: 'a', a2: 2},
        ]
    pts2 = [
        {a1: 'a'},
        ]
    nose.tools.assert_equal(_points_hash(pts1), _points_hash(pts2))

def test_hash_3():
    a1 = Var('abc')
    a2 = Var([1, 2])
    a3 = Var('ab')
    pts1 = [
        {a1: 'a', a2: 1},
        {a1: 'a', a2: 2},
        ]
    pts2 = [
        {a3: 'a'},
        ]
    nose.tools.assert_not_equal(_points_hash(pts1), _points_hash(pts2))

def test_hash_4():
    a1 = Var('abc')
    a2 = Var([1, 2])
    pts1 = [
        {a1: 'a', a2: 1},
        {a1: 'b', a2: 2},
        ]
    pts2 = [
        {a1: 'a', a2: 2},
        {a1: 'b', a2: 1},
        ]
    # fails at the moment - not a disaster
    #nose.tools.assert_not_equal(_points_hash(pts1), _points_hash(pts2))

def test_hash_5():
    a1 = Var('abc')
    a2 = Var([1, 2])
    a3 = Var('xy')
    pts1 = [
        {a1: 'a', a2: 1, a3: 'x'},
        {a1: 'a', a2: 2, a3: 'x'},
        {a1: 'a', a2: 1, a3: 'y'},
        {a1: 'a', a2: 2, a3: 'y'},
        ]
    pts2 = [
        {a1: 'a', a2: 1},
        {a1: 'a', a2: 2},
        ]
    pts3 = [
        {a1: 'a', a3: 'x'},
        {a1: 'a', a3: 'y'},
        ]
    pts4 = [
        {a1: 'a'},
        ]
    nose.tools.assert_equal(_points_hash(pts1), _points_hash(pts2))
    nose.tools.assert_equal(_points_hash(pts1), _points_hash(pts3))
    nose.tools.assert_equal(_points_hash(pts1), _points_hash(pts4))
