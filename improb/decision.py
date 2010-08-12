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

from abc import ABCMeta, abstractmethod, abstractproperty
import collections
import itertools
import numbers

from improb import PSpace, Event, Gamble

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

def dominates_pointwise(gamble, other_gamble, event=True, tolerance=1e-6):
    """Does gamble dominate other_gamble point-wise?"""
    # XXX we're ignoring the event for now
    return (all(x >= y for  x, y in zip(gamble, other_gamble))
            and any(x > y + tolerance
                    for x, y in zip(gamble, other_gamble)))

class Tree(collections.MutableMapping):
    """A decision tree.

    >>> t = Reward(5)
    >>> print(t.pspace)
    None
    >>> print(t)
    5
    >>> list(t.get_normal_form_gambles())
    [5]
    >>> t = Chance({(0,): Reward(5), (1,): Reward(6)})
    >>> t.pspace
    PSpace(2)
    >>> print(t)
    O--+--0--5
       +--1--6
    >>> list(t.get_normal_form_gambles())
    [{0: 5, 1: 6}]
    >>> t = Decision({"d1": Reward(5), "d2": Reward(6)})
    >>> print(t.pspace)
    None
    >>> list(sorted(t.get_normal_form_gambles()))
    [5, 6]
    >>> t1 = Chance({(0,1): Reward(1), (2,3): Reward(2)})
    >>> t2 = Chance({(0,1): Reward(5), (2,3): Reward(6)})
    >>> t12 = Decision({"d1": t1, "d2": t2})
    >>> t3 = Chance({(0,1): Reward(8), (2,3): Reward(9)})
    >>> t = Chance({(0,2): t12, (1,3): t3})
    >>> print(t)
    O--+--(1, 3)--O--+--(2, 3)--9
       |             +--(0, 1)--8
       +--(0, 2)--#--+--d2--O--+--(2, 3)--6
       |             |         +--(0, 1)--5
       |             +--d1--O--+--(2, 3)--2
       |             |         +--(0, 1)--1
    >>> t.pspace
    (0, 1, 2, 3)
    >>> sorted(tuple(gamble[w] for w in t.pspace) for gamble in t.get_normal_form_gambles())
    [(1, 8, 2, 9), (5, 8, 6, 9)]
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def pspace(self):
        """The possibility space, or None if there are no chance nodes
        in the tree.
        """
        raise NotImplementedError

    def check_pspace(self):
        """Check the possibility spaces.

        :raise: `exceptions.ValueError` on mismatch
        """
        if self.pspace is None:
            # no further chance nodes, is ok!
            return
        for tree in self.itervalues():
            if tree.pspace is not None and tree.pspace != self.pspace:
                raise ValueError('possibility space mismatch')
            tree.check_pspace()

    def __str__(self):
        """Return string representation of tree."""
        # note: special case for Event to make it fit on a single line
        children = [",".join(str(omega) for omega in key)
                    if isinstance(key, Event) else str(key)
                    for key in self]
        subtrees = [str(subtree).split('\n')
                    for subtree in self.itervalues()]
        width = max(len(child) for child in children) + 4
        children = ['+' + child.center(width, '-') + subtree[0]
                    for child, subtree in itertools.izip(children, subtrees)]
        children = ["\n".join([child]
                               + ["   |" + " " * width + line
                                  for line in subtree[1:]])
                    for child, subtree in itertools.izip(children, subtrees)]
        return "\n".join(children)

    @abstractmethod
    def get_normal_form_gambles(self):
        """Yield all normal form gambles."""
        raise NotImplementedError

class Reward(Tree):
    """A reward node."""
    def __init__(self, reward):
        if not isinstance(reward, numbers.Real):
            raise TypeError('specify a numeric reward')
        self.reward = reward

    @property
    def pspace(self):
        return None

    def get_normal_form_gambles(self):
        """Yield all normal form gambles."""
        yield self.reward

    def __contains__(self, key):
        return False

    def __iter__(self):
        return ()

    def __len__(self):
        return 0

    def __getitem__(self, key):
        raise ValueError('reward node has no children')

    def __setitem__(self, key, value):
        raise ValueError('reward node has no children')

    def __delitem__(self, key):
        raise ValueError('reward node has no children')

    def __str__(self):
        """Return string representation of tree."""
        return str(self.reward)

class Decision(Tree):
    """A decision tree rooted at a decision node."""
    def __init__(self, data):
        if not isinstance(data, collections.Mapping):
            raise TypeError('specify a mapping')
        if not data:
            raise ValueError('specify a non-empty mapping')
        for value in data.itervalues():
            if not isinstance(value, Tree):
                raise TypeError('children must have Tree values')
        self._data = data

    @property
    def pspace(self):
        for tree in self.itervalues():
            if tree.pspace is not None:
                return tree.pspace
        # no chance node children, so return None
        return None

    def get_normal_form_gambles(self):
        """Yield all normal form gambles."""
        for subtree in self.itervalues():
            for gamble in subtree.get_normal_form_gambles():
                yield gamble

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __str__(self):
        return "#--" + "\n   ".join(Tree.__str__(self).split("\n"))

class Chance(Tree):
    """A decision tree rooted at a chance node."""
    def __init__(self, data):
        if not isinstance(data, collections.Mapping):
            raise TypeError('specify a mapping')
        self._pspace = PSpace.make(itertools.chain(*data.keys()))
        self._data = dict(
            (self.pspace.make_event(key), value)
            for key, value in data.iteritems())

    def check_pspace(self):
        """Events of the chance nodes must form the possibility space.

        >>> t = Chance({(0,): Reward(5), (0,1): Reward(6)})
        >>> t.check_pspace()
        >>> t = Chance({(0,): Reward(5), (1,): Reward(6)})
        >>> del t[(1,)]
        >>> t.check_pspace()
        >>> t = Chance({(0,): Reward(5), (1,): Reward(6)})
        >>> t.check_pspace()
        """
        # check that there are no pairwise intersections
        union = self.pspace.make_event(False)
        for event in self:
            if union & event:
                raise ValueError('events must not intersect')
            union |= event
        # check the union
        if union != self.pspace.make_event(True):
            raise ValueError('union of events must be possibility space')
        # check the rest of the tree
        Tree.check_pspace(self)

    @property
    def pspace(self):
        return self._pspace

    def get_normal_form_gambles(self):
        """Yield all normal form gambles."""
        # note: this implementation depends on the fact that
        # iterating self.itervalues() and
        # self.iterkeys() correspond to each other
        all_gambles = itertools.product(
            *[tuple(subtree.get_normal_form_gambles())
              for subtree in self.itervalues()])
        for gambles in all_gambles:
            normal_form_gamble = {}
            for event, gamble in itertools.izip(self.iterkeys(), gambles):
                for omega in event:
                    if isinstance(gamble, numbers.Real):
                        normal_form_gamble[omega] = gamble
                    elif isinstance(gamble, dict):
                        normal_form_gamble[omega] = gamble[omega]
                    else:
                        raise RuntimeError(
                            "expected int, long, float, or dict")
            yield normal_form_gamble

    def __contains__(self, key):
        return self.pspace.make_event(key) in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[self.pspace.make_event(key)]

    def __setitem__(self, key, value):
        self._data[self.pspace.make_event(key)] = value

    def __delitem__(self, key):
        del self._data[self.pspace.make_event(key)]

    def __str__(self):
        return "O--" + "\n   ".join(Tree.__str__(self).split("\n"))
