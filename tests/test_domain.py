# -*- coding: utf-8 -*-

"""Tests for the Domain class."""

import nose.tools
import collections
import itertools

from improb import Domain, MutableDomain, Var, Set

def test_domain_bases():
    assert issubclass(Domain, collections.Set)
    assert not issubclass(Domain, collections.MutableSet)
    assert issubclass(Domain, collections.Hashable)
    assert issubclass(MutableDomain, collections.Set)
    assert issubclass(MutableDomain, collections.MutableSet)
    assert not issubclass(MutableDomain, collections.Hashable)

def test_domain_single():
    a = Var(xrange(3))
    dom = Domain(a)
    nose.tools.assert_sequence_equal(
        list(dom.points()), [{a: val} for val in xrange(3)])

def test_domain_double_1():
    a = Var(xrange(3))
    dom = Domain(a, a)
    nose.tools.assert_sequence_equal(
        list(dom.points()), [{a: val} for val in xrange(3)])

def test_domain_double_2():
    a = Var(xrange(3))
    b = Var(xrange(3))
    nose.tools.assert_not_equal(a, b)
    dom = Domain(a, b)
    nose.tools.assert_sequence_equal(
        list(dom.points()), [
            {a: x, b: y}
            for (x, y) in itertools.product(xrange(3), xrange(3))
            ]
        )

def test_domain_double_3():
    a = Var(xrange(3), name='a')
    b = Var(xrange(3), name='a') # identical to a!
    nose.tools.assert_equal(a, b)
    dom = Domain(a, b)
    nose.tools.assert_sequence_equal(
        list(dom.points()), [{a: val} for val in xrange(3)])

def test_domain_double_4():
    a = Var(xrange(3))
    b = Var('abc')
    dom = Domain(a, b)
    nose.tools.assert_sequence_equal(
        list(list(point.values()) for point in dom.points()),
        [[0, 'a'], [0, 'b'], [0, 'c'],
         [1, 'a'], [1, 'b'], [1, 'c'],
         [2, 'a'], [2, 'b'], [2, 'c']])

def test_domain_double_5():
     a = Var(['rain', 'cloudy', 'sunny'])
     b = Var(['cold', 'warm'])
     dom = Domain(a, b)
     nose.tools.assert_sequence_equal(
         list(list(point.values()) for point in dom.points()),
         [['rain', 'cold'], ['rain', 'warm'],
          ['cloudy', 'cold'], ['cloudy', 'warm'],
          ['sunny', 'cold'], ['sunny', 'warm']])

def test_domain_repr():
    a = Var([2, 4, 5], name='a')
    b = Var('xy', name='b')
    nose.tools.assert_equal(
        repr(Domain(a)),
        "Domain(Var([2, 4, 5], name='a'))")
    nose.tools.assert_equal(
        repr(Domain(a, b)),
        "Domain(Var([2, 4, 5], name='a'), Var(['x', 'y'], name='b'))")

def test_domain_str():
    a = Var([2, 4, 5])
    b = Var('uv')
    nose.tools.assert_equal(
        str(Domain(a)), "{2, 4, 5}")
    nose.tools.assert_equal(
        str(Domain(a, b)), "{2, 4, 5} × {u, v}")

def test_domain_subsets_1():
    a = Var([2, 4, 5])
    dom = Domain(a)
    nose.tools.assert_equal(
        set(dom.subsets()),
        set([
            Set([]),
            Set([{a: 2}]),
            Set([{a: 4}]),
            Set([{a: 5}]),
            Set([{a: 2}, {a: 4}]),
            Set([{a: 2}, {a: 5}]),
            Set([{a: 4}, {a: 5}]),
            Set([{}]),
            ])
        )

def test_domain_subsets_2():
    a = Var([2, 4, 5])
    dom = Domain(a)
    s = Set([{a: 2}, {a: 4}])
    nose.tools.assert_equal(
        set(dom.subsets(s)),
        set([
            Set([]),
            Set([{a: 2}]),
            Set([{a: 4}]),
            Set([{a: 2}, {a: 4}]),
            ])
        )

def test_domain_subsets_3():
    a = Var([2, 4, 5])
    dom = Domain(a)
    s = Set([{a: 2}, {a: 4}])
    nose.tools.assert_equal(
        set(dom.subsets(s, empty=False, full=False)),
        set([
            Set([{a: 2}]),
            Set([{a: 4}]),
            ])
        )

def test_domain_subsets_4():
    a = Var([2, 4, 5])
    dom = Domain(a)
    s = Set([{a: 4}])
    nose.tools.assert_equal(
        set(dom.subsets(contains=s)),
        set([
            Set([{a: 4}]),
            Set([{a: 2}, {a: 4}]),
            Set([{a: 4}, {a: 5}]),
            Set([{}]),
            ])
        )

def test_mutable_domain_1():
    a = Var(xrange(3))
    dom = MutableDomain(a)
    nose.tools.assert_sequence_equal(
        list(dom.points()), [{a: val} for val in xrange(3)])
    b = Var('abc')
    dom.add(b)
    nose.tools.assert_sequence_equal(
        list(dom.points()), [
            {a: x, b: y}
            for (x, y) in itertools.product(xrange(3), 'abc')
            ]
        )
