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

"""Decision trees."""

from abc import ABCMeta, abstractmethod, abstractproperty
import cdd # NumberTypeable
import collections
import itertools
import numbers

from improb import PSpace, Event, Gamble
from improb._compat import OrderedDict
from improb.decision.opt import Opt

class Tree(collections.MutableMapping):
    r"""A decision tree.

    >>> t = Reward(5)
    >>> print(t.pspace)
    None
    >>> print(t)
    :5.0
    >>> list(t.get_normal_form())
    [(5.0, Reward(5.0, number_type='float'))]
    >>> t = Chance(pspace=(0, 1), data={(0,): Reward(5), (1,): Reward(6)})
    >>> t.pspace
    PSpace(2)
    >>> t.get_number_type()
    'float'
    >>> print(t)
    O--(0)--:5.0
       |
       (1)--:6.0
    >>> list(gamble for gamble, normal_tree in t.get_normal_form())
    [Gamble(pspace=PSpace(2), mapping={0: 5.0, 1: 6.0})]
    >>> t = Decision({"d1": Reward(5),
    ...               "d2": Reward(6)})
    >>> print(t.pspace)
    None
    >>> print(t) # dict can change ordering
    #--d2--:6.0
       |
       d1--:5.0
    >>> for gamble, normal_tree in sorted(t.get_normal_form()):
    ...     print(gamble)
    5.0
    6.0
    >>> for gamble, normal_tree in sorted(t.get_normal_form()):
    ...     print(normal_tree)
    #--d1--:5.0
    #--d2--:6.0
    >>> pspace = PSpace(4)
    >>> t1 = Chance(pspace)
    >>> t1[(0,1)] = Reward(1, 'fraction')
    >>> t1[(2,3)] = Reward(2, 'fraction')
    >>> t2 = Chance(pspace)
    >>> t2[(0,1)] = Reward(5, 'fraction')
    >>> t2[(2,3)] = Reward(6, 'fraction')
    >>> t12 = Decision()
    >>> t12["d1"] = t1
    >>> t12["d2"] = t2
    >>> t3 = Chance(pspace)
    >>> t3[(0,1)] = Reward(8, 'fraction')
    >>> t3[(2,3)] = Reward(9, 'fraction')
    >>> t = Chance(pspace)
    >>> t[(0,2)] = t12
    >>> t[(1,3)] = t3
    >>> print(t)
    O--(0,2)--#--d1--O--(0,1)--:1
       |         |      |
       |         |      (2,3)--:2
       |         |
       |         d2--O--(0,1)--:5
       |                |
       |                (2,3)--:6
       |
       (1,3)--O--(0,1)--:8
                 |
                 (2,3)--:9
    >>> t.pspace
    PSpace(4)
    >>> for gamble, normal_tree in t.get_normal_form():
    ...     print(gamble)
    ...     print('')
    0 : 1
    1 : 8
    2 : 2
    3 : 9
    <BLANKLINE>
    0 : 5
    1 : 8
    2 : 6
    3 : 9
    <BLANKLINE>
    >>> for gamble, normal_tree in t.get_normal_form():
    ...     print(normal_tree)
    ...     print('')
    O--(0,2)--#--d1--O--(0,1)--:1
       |                |
       |                (2,3)--:2
       |
       (1,3)--O--(0,1)--:8
                 |
                 (2,3)--:9
    <BLANKLINE>
    O--(0,2)--#--d2--O--(0,1)--:5
       |                |
       |                (2,3)--:6
       |
       (1,3)--O--(0,1)--:8
                 |
                 (2,3)--:9
    <BLANKLINE>
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def pspace(self):
        """The possibility space, or None if there are no chance nodes
        in the tree.
        """
        raise NotImplementedError

    def get_number_type(self):
        for subtree in self.itervalues():
            # this just picks the first reward node
            return subtree.get_number_type()

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
        children = [key.name if isinstance(key, Event) else str(key)
                    for key in self]
        subtrees = [str(subtree).split('\n')
                    for subtree in self.itervalues()]
        width = max(len(child) for child in children) + 2
        children = [child.ljust(width, '-') + subtree[0]
                    for child, subtree in itertools.izip(children, subtrees)]
        children = (
            ["\n".join([child]
                       + ["|" + " " * (width - 1) + line
                          for line in subtree[1:]]
                       + ["|"])
             for child, subtree
             in itertools.izip(children[:-1], subtrees[:-1])]
            +
            ["\n".join([child]
                       + [" " * width + line
                          for line in subtree[1:]])
             for child, subtree
             in itertools.izip(children[-1:], subtrees[-1:])]
            )
        
        return "\n".join(children)

    def get_normal_form(self):
        """Yield normal form as (gamble, tree) pairs, where the tree
        represents the normal form decision corresponding to the gamble.
        """
        # get_norm_back_opt without optimality operator gives exactly all
        # normal form gambles!
        return self._get_norm_back_opt()

    def get_norm_opt(self, opt=None, event=True):
        """Normal form optimality with respect to a given optimality
        operator, conditional on the given event.
        """
        if opt is None:
            for gamble, normal_tree in self._get_norm_back_opt():
                yield gamble, normal_tree
        elif not isinstance(opt, Opt):
            raise TypeError("expected a subclass of Opt")
        else:
            normal_form = list(self._get_norm_back_opt())
            opt_gambles = set(
                opt((gamble for gamble, tree in normal_form), event))
            for gamble, normal_tree in normal_form:
                if gamble in opt_gambles:
                    yield gamble, normal_tree

    def get_norm_back_opt(self, opt=None, event=True):
        """Yield optimal solution by normal form backward induction,
        as (gamble, tree) pairs, where the tree represents the normal
        form decision corresponding to the gamble.
        """
        if opt is None:
            for gamble, normal_tree in self._get_norm_back_opt():
                yield gamble, normal_tree
        elif not isinstance(opt, Opt):
            raise TypeError("expected a subclass of Opt")
        else:
            _norm_back_opt = list(self._get_norm_back_opt(opt, event))
            opt_gambles = set(
                opt((gamble for gamble, tree in _norm_back_opt), event))
            for gamble, normal_tree in _norm_back_opt:
                if gamble in opt_gambles:
                    yield gamble, normal_tree

    @abstractmethod
    def _get_norm_back_opt(self, opt=None, event=True):
        """This is the core implementation of get_norm_back_opt: it is
        get_norm_back_opt but without applying opt at the root of the tree.
        """
        raise NotImplementedError

    @abstractmethod
    def __add__(self, value):
        """Add a value to all final reward nodes."""
        raise NotImplementedError

    @abstractmethod
    def __sub__(self, value):
        """Substract a value from all final reward nodes."""
        raise NotImplementedError

class Reward(Tree, cdd.NumberTypeable):
    """A reward node."""
    def __init__(self, reward, number_type='float'):
        cdd.NumberTypeable.__init__(self, number_type)
        if not isinstance(reward, numbers.Real):
            raise TypeError('specify a numeric reward')
        self.reward = self.make_number(reward)

    @property
    def pspace(self):
        return None

    def get_number_type(self):
        return self.number_type

    def _get_norm_back_opt(self, opt=None, event=True):
        yield self.reward, self

    def __contains__(self, key):
        return False

    def __iter__(self):
        return iter([]) # empty iterator

    def __len__(self):
        return 0

    def __getitem__(self, key):
        raise ValueError('reward node has no children')

    def __setitem__(self, key, value):
        raise ValueError('reward node has no children')

    def __delitem__(self, key):
        raise ValueError('reward node has no children')

    def __str__(self):
        return ":" + self.number_str(self.reward)

    def __repr__(self):
        return "Reward({0}, number_type='{1}')".format(
            self.number_repr(self.reward),
            self.number_type)

    def __add__(self, value):
        return Reward(self.reward + self.make_number(value),
                      number_type=self.number_type)

    def __sub__(self, value):
        return Reward(self.reward - self.make_number(value),
                      number_type=self.number_type)

class Decision(Tree):
    """A decision tree rooted at a decision node.

    :param data: Mapping from decisions (i.e. strings, but any
        immutable object would work) to trees.
    :type data: `collections.Mapping`
    """
    def __init__(self, data=None):
        self._data = OrderedDict()
        # check type
        if isinstance(data, collections.Mapping):
            for key, value in data.iteritems():
                if not isinstance(value, Tree):
                    raise TypeError('children must have Tree values')
                self[key] = value
        elif data is not None:
            raise TypeError('specify a mapping')

    @property
    def pspace(self):
        for subtree in self.itervalues():
            if subtree.pspace is not None:
                return subtree.pspace
        # no chance node children, so return None
        return None

    def _get_norm_back_opt(self, opt=None, event=True):
        for decision, subtree in self.iteritems():
            for gamble, normal_subtree in subtree.get_norm_back_opt(opt, event):
                yield gamble, Decision(data={decision: normal_subtree})

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

    def __repr__(self):
        return (
            "Decision({"
            + ", ".join("{0}: {1}".format(repr(key), repr(value))
                      for key, value in self.iteritems())
            + "})"
            )

    def __add__(self, value):
        return Decision(
            OrderedDict((decision, subtree + value)
                        for decision, subtree in self.iteritems()))

    def __sub__(self, value):
        return Decision(
            OrderedDict((decision, subtree - value)
                        for decision, subtree in self.iteritems()))

class Chance(Tree):
    """A decision tree rooted at a chance node.

    :param pspace: The possibility space.
    :type pspace: |pspacetype|
    :param data: Mapping from events to trees (optional).
    :type data: `collections.Mapping`
    """
    def __init__(self, pspace, data=None):
        self._data = OrderedDict()
        self._pspace = PSpace.make(pspace)
        # extract data
        if isinstance(data, collections.Mapping):
            for key, value in data.iteritems():
                self[key] = value
        elif data is not None:
            raise TypeError('data must be a mapping')

    def check_pspace(self):
        """Events of the chance nodes must form the possibility space.

        >>> t = Chance(pspace=(0,1), data={(0,): Reward(5), (0,1): Reward(6)})
        >>> t.check_pspace() # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> t = Chance(pspace=(0,1), data={(0,): Reward(5)})
        >>> t.check_pspace() # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> t = Chance(pspace=(0,1), data={(0,): Reward(5), (1,): Reward(6)})
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

    def _get_norm_back_opt(self, opt=None, event=True):
        number_type = self.get_number_type()
        # note: this implementation depends on the fact that
        # iterating self.itervalues() and
        # self.iterkeys() correspond to each other
        all_normal_forms = itertools.product(
            *[tuple(subtree.get_norm_back_opt())
              for subtree in self.itervalues()])
        for normal_forms in all_normal_forms:
            data = {}
            tree = OrderedDict()
            for event, (gamble, normal_subtree) in itertools.izip(
                self.iterkeys(), normal_forms):
                for omega in event:
                    if isinstance(gamble, numbers.Real):
                        data[omega] = gamble
                    elif isinstance(gamble, Gamble):
                        data[omega] = gamble[omega]
                    else:
                        raise RuntimeError(
                            "expected int, long, float, or Gamble")
                tree[event] = normal_subtree
            yield (Gamble(pspace=self.pspace,
                          data=data,
                          number_type=number_type),
                   Chance(pspace=self.pspace,
                          data=tree))

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

    def __repr__(self):
        return (
            "Chance("
            + "pspace={0}".format(repr(self.pspace))
            + ", data={"
            + ", ".join("{0}: {1}".format(repr(key), repr(value))
                      for key, value in self.iteritems())
            + "})"
            )

    def __add__(self, value):
        return Chance(
            self.pspace,
            OrderedDict((event, subtree + value)
                        for event, subtree in self.iteritems()))

    def __sub__(self, value):
        return Chance(
            self.pspace,
            OrderedDict((event, subtree - value)
                         for event, subtree in self.iteritems()))
