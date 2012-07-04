"""Tests for the Domain class."""

import nose.tools
import itertools

from improb import Domain, Var

def test_domain_single():
    a = Var(xrange(3))
    dom = Domain(a)
    nose.tools.assert_sequence_equal(
        list(dom.atoms()), [{a: val} for val in xrange(3)])

def test_domain_double_1():
    a = Var(xrange(3))
    dom = Domain(a, a)
    nose.tools.assert_sequence_equal(
        list(dom.atoms()), [{a: val} for val in xrange(3)])

def test_domain_double_2():
    a = Var(xrange(3))
    b = Var(xrange(3))
    nose.tools.assert_not_equal(a, b)
    dom = Domain(a, b)
    nose.tools.assert_sequence_equal(
        list(dom.atoms()), [
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
        list(dom.atoms()), [{a: val} for val in xrange(3)])

def test_domain_double_4():
    a = Var(xrange(3))
    b = Var('abc')
    dom = Domain(a, b)
    nose.tools.assert_sequence_equal(
        list(list(atom.values()) for atom in dom.atoms()),
        [[0, 'a'], [0, 'b'], [0, 'c'],
         [1, 'a'], [1, 'b'], [1, 'c'],
         [2, 'a'], [2, 'b'], [2, 'c']])

def test_domain_double_5():
     a = Var(['rain', 'cloudy', 'sunny'])
     b = Var(['cold', 'warm'])
     dom = Domain(a, b)
     nose.tools.assert_sequence_equal(
         list(list(atom.values()) for atom in dom.atoms()),
         [['rain', 'cold'], ['rain', 'warm'],
          ['cloudy', 'cold'], ['cloudy', 'warm'],
          ['sunny', 'cold'], ['sunny', 'warm']])
