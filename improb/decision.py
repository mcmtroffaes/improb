# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2010, Matthias Troffaes
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""A module with utility functions for decision making."""

import itertools

from improb import _make_tuple

def filter_maximal(set_, dominates, *args):
    """Filter elements that are maximal according to the given
    partial ordering.

    >>> list(filter_maximal([[0,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], dominates_pointwise))
    [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    >>> list(filter_maximal([3,2,9,6,16,9.1,16,5.3], lambda x, y: x > y))
    [16, 16]
    >>> list(filter_maximal([set([0,1]), set([1]), set([0]), set([1,2]), set([1,2,3])], lambda x, y: x > y))
    [set([0, 1]), set([1, 2, 3])]
    """
    # keep track of maximal elements
    maximal_elements = []
    # make a stack of all possibly maximal elements
    elements = list(set_)
    while elements:
        # pop a candidate maximal element from the stack
        element = elements.pop(0)
        # compare element against other maximal elements
        for other_element in maximal_elements:
            if dominates(other_element, element, *args):
                # not maximal
                break
        else:
            # compare element against remaining possibly maximal elements
            for other_i, other_element in enumerate(elements):
                if dominates(other_element, element, *args):
                    # not maximal
                    break
            else:
                # we found a maximal one!
                yield element
                maximal_elements.append(element)

def dominates_pointwise(gamble, other_gamble, event=None, tolerance=1e-6):
    """Does gamble dominate other_gamble point-wise?"""
    # XXX we're ignoring the event for now
    return (all(x >= y for  x, y in zip(gamble, other_gamble))
            and any(x > y + tolerance
                    for x, y in zip(gamble, other_gamble)))

class Tree:
    """A decision tree. Decisions are strings, events are frozensets,
    rewards are floats or ints.

    >>> t = Tree(5)
    >>> print(t.pspace)
    None
    >>> list(t.get_normal_form_gambles())
    [5]
    >>> t = Tree(children={frozenset([0]): Tree(5), frozenset([1]): Tree(6)})
    >>> t.pspace
    (0, 1)
    >>> list(t.get_normal_form_gambles())
    [{0: 5, 1: 6}]
    >>> t = Tree(children={"d1": Tree(5), "d2": Tree(6)})
    >>> print(t.pspace)
    None
    >>> list(sorted(t.get_normal_form_gambles()))
    [5, 6]
    >>> t1 = Tree(children={frozenset([0, 1]): Tree(1), frozenset([2, 3]): Tree(2)})
    >>> t2 = Tree(children={frozenset([0, 1]): Tree(5), frozenset([2, 3]): Tree(6)})
    >>> t12 = Tree(children={"d1": t1, "d2": t2})
    >>> t3 = Tree(children={frozenset([0, 1]): Tree(8), frozenset([2, 3]): Tree(9)})
    >>> t = Tree(children={frozenset([0, 2]): t12, frozenset([1, 3]): t3})
    >>> t.pspace
    (0, 1, 2, 3)
    >>> sorted(tuple(gamble[w] for w in t.pspace) for gamble in t.get_normal_form_gambles())
    [(1, 8, 2, 9), (5, 8, 6, 9)]
    """
    def __init__(self, children=None):
        if not isinstance(children, (int, long, float, dict)):
            raise TypeError("children must be int, long, float, or dict")
        self.children = children
        if self.is_reward_node:
            self.pspace = None
        elif self.is_chance_node:
            # check that children form a partition
            pspace = set()
            for event in self.children:
                assert(isinstance(event, frozenset))
                assert(not(pspace & event))
                pspace |= event
            self.pspace = tuple(sorted(pspace))
            # check that children have correct possibility space
            for subtree in self.children.itervalues():
                if subtree.pspace is not None:
                    assert(subtree.pspace == self.pspace)
        elif self.is_decision_node:
            # check that children share possibility space
            pspace = None
            for dec, subtree in self.children.iteritems():
                if subtree.pspace is not None:
                    # grap the first dec.pspace that isn't None
                    if pspace is None:
                        pspace = subtree.pspace
                    else:
                        assert(pspace == subtree.pspace)
                # store it
                self.pspace = pspace

    @property
    def is_reward_node(self):
        """Is the tree a reward?"""
        return isinstance(self.children, (int, long, float))

    @property
    def is_chance_node(self):
        """Is the tree's root a chance node?"""
        return (isinstance(self.children, dict)
                and any(isinstance(child, frozenset)
                        for child in self.children))

    @property
    def is_decision_node(self):
        """Is the tree's root a decision node?"""
        return (isinstance(self.children, dict)
                and any(isinstance(child, str) for child in self.children))

    def get_normal_form_gambles(self):
        if self.is_reward_node:
            yield self.children
        elif self.is_chance_node:
            # note: this implementation depends on the fact that
            # iterating self.children.itervalues() and
            # self.children.iterkeys() correspond to each other
            all_gambles = itertools.product(
                *[tuple(subtree.get_normal_form_gambles())
                  for subtree in self.children.itervalues()])
            for gambles in all_gambles:
                normal_form_gamble = {}
                for event, gamble in itertools.izip(self.children.iterkeys(),
                                                    gambles):
                    for omega in event:
                        if isinstance(gamble, (int, long, float)):
                            normal_form_gamble[omega] = gamble
                        elif isinstance(gamble, dict):
                            normal_form_gamble[omega] = gamble[omega]
                        else:
                            raise RuntimeError(
                                "expected int, long, float, or dict")
                yield normal_form_gamble
        elif self.is_decision_node:
            for subtree in self.children.itervalues():
                for gamble in subtree.get_normal_form_gambles():
                    yield gamble
