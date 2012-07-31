# -*- coding: utf-8 -*-
"""Tests for the SetFunction class."""

from __future__ import division, print_function

import nose.tools
import itertools

from improb import Var, Domain, Set, Func
from improb.setfunction import SetFunction
from fractions import Fraction

def test_setfunc_str_repr_0():
    a = Var([0, 1, 2], name='A')
    sf = SetFunction(
        data={
            Set([]): 1,
            Set([{a: 0}, {a: 2}]): 2.1,
            Set([{}]): 1/3})
    nose.tools.assert_equal(
        str(sf), """\
{∅: 1,
 Ω: 0.333333333333,
 A=2 | A=0: 2.1}""")
    nose.tools.assert_equal(
        repr(sf),
        "SetFunction(data={Set([]): 1, "
        "Set([{}]): 0.3333333333333333, "
        "Set([{Var([0, 1, 2], name='A'): 2}, {Var([0, 1, 2], name='A'): 0}]): 2.1})")

def test_setfunc_str_repr_1():
    a = Var('ab', 'A')
    sf = SetFunction(data={
        Set([]): 0,
        Set([{a: 'a'}]): 0.25,
        Set([{a: 'b'}]): 0.3,
        Set([{}]): 1,
        })
    nose.tools.assert_equal(
        str(sf), """\
{Ω: 1,
 ∅: 0,
 A=b: 0.3,
 A=a: 0.25}""")

def test_setfunc_mobius_0():
    a = Var('ab', 'A')
    sf = SetFunction(data={
        Set([]): 0,
        Set([{a: 'a'}]): Fraction(1, 4),
        Set([{a: 'b'}]): Fraction(3, 10),
        Set([{}]): 1,
        })
    inv = SetFunction(data=dict(
        (event, sf.get_mobius(event))
        for event in sf.domain.subsets()))
    nose.tools.assert_equal(
        inv, SetFunction(data={
            Set([]): 0,
            Set([{a: 'a'}]): Fraction(1, 4),
            Set([{a: 'b'}]): Fraction(3, 10),
            Set([{}]): Fraction(9, 20),
            }))

def test_setfunc_mobius_1():
    a = Var('abc', 'A')
    sf = SetFunction(data={
        Set([]): 0,
        Set([{a: 'a'}]): Fraction(1, 4),
        Set([{a: 'b'}]): Fraction(1, 2),
        Set([{a: 'a'}, {a: 'b'}]): Fraction(1, 3),
        Set([{}]): 1,
        })
    # also checks that it does not raise
    nose.tools.assert_equal(
        sf.get_mobius(Set([{a: 'a'}, {a: 'b'}])), Fraction(-5, 12))
    nose.tools.assert_raises(
        KeyError, lambda: sf.get_mobius(Set([{a: 'b'}, {a: 'c'}])))

def test_setfunc_zeta_0():
    a = Var('ab', 'A')
    setfunc = SetFunction(data={
        Set([]): 0,
        Set([{a: 'a'}]): Fraction(1, 4),
        Set([{a: 'b'}]): Fraction(3, 10),
        Set([{}]): Fraction(9, 20),
        })
    inv = SetFunction(data=dict((event, setfunc.get_zeta(event))
                                for event in setfunc.domain.subsets()))
    nose.tools.assert_equal(
        inv, SetFunction(data={
            Set([]): 0,
            Set([{a: 'a'}]): Fraction(1, 4),
            Set([{a: 'b'}]): Fraction(3, 10),
            Set([{}]): 1,
            }))

def test_setfunc_choquet_0():
    a = Var('abc')
    s = SetFunction(data={
        Set([]): 0,
        Set([{a: 'a'}]): 0,
        Set([{a: 'b'}]): 0,
        Set([{a: 'c'}]): 0,
        Set([{a: 'a'}, {a: 'b'}]): .5,
        Set([{a: 'a'}, {a: 'c'}]): .5,
        Set([{a: 'b'}, {a: 'c'}]): .5,
        Set([{}]): 1})
    nose.tools.assert_equal(s.get_choquet(Func(a, [1, 2, 3])), 1.5)
    nose.tools.assert_equal(s.get_choquet(Func(a, [1, 2, 2])), 1.5)
    nose.tools.assert_equal(s.get_choquet(Func(a, [1, 2, 1])), 1)

def test_setfunc_choquet_1():
    a = Var('abc', name='A')
    s = SetFunction(data={
        Set([{a: 'a'}, {a: 'b'}]): .5,
        Set([{a: 'a'}, {a: 'c'}]): .5,
        Set([{a: 'b'}, {a: 'c'}]): .5,
        Set([{}]): 1})
    nose.tools.assert_equal(s.get_choquet(Func(a, [1, 2, 2])), 1.5)
    nose.tools.assert_equal(s.get_choquet(Func(a, [2, 2, 1])), 1.5)
    nose.tools.assert_equal(s.get_choquet(Func(a, [-1, -1, -2])), -1.5)
    nose.tools.assert_raises(
        KeyError, lambda: s.get_choquet(Func(a, [1, 2, 3])))

def test_setfunc_make_extreme_bba_n_monotone_32():
    a = Var('abc')
    dom = Domain(a)
    bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=2))
    nose.tools.assert_equal(len(bbas), 8)
    nose.tools.assert_true(all(bba.is_bba_n_monotone(2) for bba in bbas))
    nose.tools.assert_false(all(bba.is_bba_n_monotone(3) for bba in bbas))

def test_setfunc_make_extreme_bba_n_monotone_33():
    a = Var('abc')
    dom = Domain(a)
    bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=3))
    nose.tools.assert_equal(len(bbas), 7)
    nose.tools.assert_true(all(bba.is_bba_n_monotone(2) for bba in bbas))
    nose.tools.assert_true(all(bba.is_bba_n_monotone(3) for bba in bbas))

@nose.plugins.attrib.attr(slow=True)
def test_setfunc_make_extreme_bba_n_monotone_42():
    a = Var('abcd')
    dom = Domain(a)
    bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=2))
    nose.tools.assert_equal(len(bbas), 41)
    nose.tools.assert_true(all(bba.is_bba_n_monotone(2) for bba in bbas))
    nose.tools.assert_false(all(bba.is_bba_n_monotone(3) for bba in bbas))
    nose.tools.assert_false(all(bba.is_bba_n_monotone(4) for bba in bbas))

@nose.plugins.attrib.attr(slow=True)
def test_setfunc_make_extreme_bba_n_monotone_43():
    a = Var('abcd')
    dom = Domain(a)
    bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=3))
    nose.tools.assert_equal(len(bbas), 16)
    nose.tools.assert_true(all(bba.is_bba_n_monotone(2) for bba in bbas))
    nose.tools.assert_true(all(bba.is_bba_n_monotone(3) for bba in bbas))
    nose.tools.assert_false(all(bba.is_bba_n_monotone(4) for bba in bbas))

@nose.plugins.attrib.attr(slow=True)
def test_setfunc_make_extreme_bba_n_monotone_44():
    a = Var('abcd')
    dom = Domain(a)
    bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=4))
    nose.tools.assert_equal(len(bbas), 15)
    nose.tools.assert_true(all(bba.is_bba_n_monotone(2) for bba in bbas))
    nose.tools.assert_true(all(bba.is_bba_n_monotone(3) for bba in bbas))
    nose.tools.assert_true(all(bba.is_bba_n_monotone(4) for bba in bbas))
