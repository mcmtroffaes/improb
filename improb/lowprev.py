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

"""A module for working with lower previsions."""

from __future__ import division

import itertools
import pycddlib
import random
import scipy.optimize

def _make_tuple(pspace):
    """Convert argument into a tuple, useful for possibility space."""
    if pspace is None:
        return (0, 1)
    elif isinstance(pspace, int):
        return tuple(xrange(pspace))
    else:
        return tuple(pspace)

class LowPrev:
    """A class for lower previsions.

    This class implements a lower prevision as a sequence of half-spaces.
    These half-spaces constrain a convex set of probability mass functions.
    Each half-space is represented by a gamble, and a number (i.e. its lower
    expectation/prevision).

    Add half-space constraints by calling for instance the
    L{set_lower} and L{set_upper} functions. Calculate the natural extension
    with the L{get_lower} and L{get_upper} functions.

    Example
    =======

    >>> import lowprev
    >>> import decision
    >>> lpr = lowprev.LowPrev(4)
    >>> lpr.set_lower([4,2,1,0], 3)
    >>> lpr.set_upper([4,1,2,0], 3)
    >>> lpr.is_avoiding_sure_loss()
    True
    >>> lpr.is_coherent()
    True
    >>> lpr.is_linear()
    False
    >>> print(lpr.get_lower([1,0,0,0]))
    0.5
    >>> print(lpr.get_upper([1,0,0,0]))
    0.75
    >>> list(lpr)
    [([4.0, 2.0, 1.0, 0.0], 3.0), ([-4.0, -1.0, -2.0, 0.0], -3.0)]
    >>> list(decision.filter_maximal([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], lpr.dominates))
    [[1, 0, 0, 0], [0, 1, 0, 0]]
    >>> list(decision.filter_maximal([[0,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]], lpr.dominates))
    [[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    """

    def __init__(self, pspace=None):
        """Construct vacuous lower prevision on possibility space of given
        size.

        @param pspace: The possibility space.
        @type pspace: int, or iterable
        """
        self._pspace = _make_tuple(pspace)
        self._matrix = pycddlib.Matrix([[+1] + [-1] * self.num_states,
                                        [-1] + [+1] * self.num_states]
                                        +
                                        [[0] + [1 if i == j else 0
                                                for i in self.states]
                                         for j in self.states])

    @property
    def pspace(self):
        return self._pspace

    @property
    def num_states(self):
        return len(self._pspace)

    @property
    def states(self):
        return xrange(self.num_states)

    def set_lower(self, gamble, lprev):
        """Constrain the expectation of C{gamble} to be at least C{lprev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param lprev: The lower bound for this expectation.
        @type lprev: float/int
        """
        self._matrix.append_rows([[-lprev] + gamble])

    def set_upper(self, gamble, uprev):
        """Constrain the expectation of C{gamble} to be at most C{uprev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param uprev: The upper bound for this expectation.
        @type uprev: float/int
        """
        self._matrix.append_rows([[uprev] + [-value for value in gamble]])

    def set_precise(self, gamble, prev):
        """Constrain the expectation of C{gamble} to be exactly C{prev}.

        @param gamble: The gamble whose expectation to bound.
        @type gamble: list of floats/ints
        @param prev: The precise bound for this expectation.
        @type prev: float/int
        """
        self.set_lower(gamble, prev)
        self.set_upper(gamble, prev)

    def __iter__(self):
        """Yield tuples (gamble, lprev)."""
        for rownum in xrange(self.num_states + 2, self._matrix.rowsize):
            row = self._matrix[rownum]
            yield row[1:], -row[0]

    def get_lower(self, gamble, event=None, tolerance=1e-6):
        """Return the lower expectation for C{gamble} via natural extension.

        @param gamble: The gamble whose lower expectation to find.
        @type gamble: list of floats/ints
        @return: The lower bound for this expectation, i.e. the natural
            extension of the gamble.
        """
        if event is None:
            self._matrix.set_lp_obj_type(pycddlib.LPOBJ_MIN)
            self._matrix.set_lp_obj_func([0] + [gamble[w] for w in self.pspace])
            #print self._matrix # DEBUG
            linprog = pycddlib.LinProg(self._matrix)
            linprog.solve()
            #print linprog # DEBUG
            if linprog.status == pycddlib.LPSTATUS_OPTIMAL:
                return linprog.opt_value
            elif linprog.status == pycddlib.LPSTATUS_INCONSISTENT:
                raise ValueError("lower prevision incurs sure loss")
            else:
                raise RuntimeError("BUG: unexpected status (%i)" % linprog.status)
        else:
            lowprev_event = self.get_lower(
                [1 if w in event else 0 for w in self.pspace])
            if lowprev_event < tolerance:
                raise ZeroDivisionError(
                    "cannot condition on event with zero lower probability")
            return scipy.optimize.brentq(
                f=lambda mu: self.get_lower(
                    [gamble[w] - mu if w in event else 0
                     for w in self.pspace]),
                a=min(gamble[w] for w in event),
                b=max(gamble[w] for w in event))

    def get_upper(self, gamble, event=None):
        """Return the upper expectation for C{gamble} via natural extension.

        @param gamble: The gamble whose upper expectation to find.
        @type gamble: list of floats/ints
        @return: The upper bound for this expectation, i.e. the natural
            extension of the gamble.
        """
        return -self.get_lower(dict((w, -gamble[w]) for w in self.pspace), event)

    #def getcredalset(self):
    #    """Find credal set corresponding to this lower prevision."""
    #    raise NotImplementedError

    def is_avoiding_sure_loss(self):
        """No Dutch book? Does the lower prevision avoid sure loss?

        @return: C{True} if the lower prevision avoids sure loss, C{False}
            otherwise.
        """
        try:
            self.get_lower(dict((w, 0) for w in self.pspace))
        except ValueError:
            return False
        return True

    def is_coherent(self, tolerance=1e-6):
        """Do all assessments coincide with their natural extension? Is the
        lower prevision coherent?"""
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss():
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, lprev in self:
            if self.get_lower(gamble) > lprev + tolerance:
                return False
        return True

    def is_linear(self, tolerance=1e-6):
        """Is the lower prevision a linear prevision? More precisely,
        we check that the natural extension is linear on the linear
        span of the domain of the lower prevision.
        """
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss():
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, lprev in self:
            # implementation note: if upper - lower <= tolerance then
            # obviously lprev is within tolerance of the lower and the
            # upper as well, so we can keep lprev out of the picture
            # when checking for linearity (of course, it's taken into
            # account when calculating the natural extension)
            if self.get_upper(gamble) - self.get_lower(gamble) > tolerance:
                return False
        return True

    def dominates(self, gamble, other_gamble, event=None, tolerance=1e-6):
        """Does gamble dominate other_gamble in lower prevision?"""
        return (
            self.get_lower(
                dict((w, gamble[w] - other_gamble[w])
                     for w in self.pspace),
                event)
                > tolerance)

    def get_mobius_inverse(self):
        """Return the mobius inverse of the lower probability determined by
        this lower prevision. This usually only makes sense for completely
        monotone lower previsions.

        >>> lpr = LowPrev(2)
        >>> lpr.set_lower([1,0], 0.3)
        >>> lpr.set_lower([0,1], 0.2)
        >>> mass = lpr.get_mobius_inverse()
        >>> print(mass[frozenset()])
        0.0
        >>> print(mass[frozenset([0])])
        0.3
        >>> print(mass[frozenset([1])])
        0.2
        >>> print(mass[frozenset([0,1])])
        0.5
        """
        set_ = set(self.pspace)
        map_ = {}
        for event in subsets(set_):
            map_[event] = self.get_lower(
                dict((w, 1 if w in event else 0)
                     for w in self.pspace))
        return mobius_inverse(map_, set_)

    #def optimize(self):
    #    """Removes redundant assessments."""
    #    raise NotImplementedError

    #def __cmp__(self, lowprev):
    #    """Compares two lower previsions, checking for dominance."""
    #    raise NotImplementedError

    #def __iand__(self, lowprev):
    #    """Conjunction. Result is not necessarily coherent, and incurs sure
    #    loss if conjunction does not exist."""
    #    raise NotImplementedError

    #def __ior__(self, lowprev):
    #    """Disjunction (unanimity rule). Result is not necessarily
    #    coherent."""
    #    raise NotImplementedError

def random_lowprob(numstates=2, division=None):
    """Generate a random coherent lower probability."""
    # for now this is just a pretty dumb method
    events = [list(event)
              for event in itertools.product([0, 1], repeat=numstates)]
    while True:
        lpr = LowPrev(numstates)
        for event in events:
            if sum(event) == 0:
                continue
            if sum(event) == numstates:
                continue
            if division is None:
                # a number between 0 and 1 / sum(event)
                lpr.set_lower(event, random.random() / sum(event))
            else:
                # a number between 0 and 1 / sum(event), but discretized
                lpr.set_lower(event,
                              random.randint(0,
                                             division * sum(event)
                                             // numstates)
                              / division)
        if lpr.is_avoiding_sure_loss():
           return lpr

class LinVac(LowPrev):
    """Linear-vacuous mixture.

    >>> lpr = LinVac([0.2, 0.4, 0.5], 0.1) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: probabilities must sum to one

    >>> lpr = LinVac([0.2, 0.3, 0.5], 0.1)
    >>> print lpr.get_lower([1,0,0])
    0.18
    >>> print lpr.get_lower([0,1,0])
    0.27
    >>> print lpr.get_lower([0,0,1])
    0.45
    >>> print lpr.get_lower([3,2,1])
    1.63
    >>> print lpr.get_upper([3,2,1])
    1.83

    >>> lpr = LinVac([0.42, 0.08, 0.18, 0.32], 0.1)
    >>> print lpr.get_lower([5,5,-5,-5])
    -0.5
    >>> print lpr.get_lower([5,5,-5,-5], set([0,2])) # (6 - 31 * 0.1) / (3 + 2 * 0.1)
    0.90625
    >>> print lpr.get_lower([-5,-5,5,5], set([1,3])) # (6 - 31 * 0.1) / (2 + 3 * 0.1) # doctest: +ELLIPSIS
    1.260869...
    >>> print lpr.get_lower([0,5,0,-5]) # -(6 + 19 * 0.1) / 5
    -1.58
    >>> print lpr.get_lower([0,-5,0,5]) # (6 - 31 * 0.1) / 5
    0.58
    """
    def __init__(self, prob, epsilon):
        if isinstance(prob, (list, tuple)):
            tot = sum(prob)
            self._pspace = tuple(xrange(len(prob)))
        elif isinstance(prob, dict):
            tot = sum(prob.itervalues())
            self._pspace = tuple(w for w in prob)
        if tot < 1 - 1e-6 or tot > 1 + 1e-6:
            raise ValueError("probabilities must sum to one")
        self._prob = prob
        self._epsilon = epsilon
        self._matrix = None

    def __iter__(self):
        raise NotImplementedError

    def set_lower(self, gamble):
        raise NotImplementedError

    def set_upper(self, gamble):
        raise NotImplementedError
    
    def set_precise(self, gamble):
        raise NotImplementedError

    def get_lower(self, gamble, event=None):
        if event is None:
            event = set(self.pspace)
        return (
            ((1 - self._epsilon) * sum(self._prob[w] * gamble[w] for w in event)
             + self._epsilon * min(gamble[w] for w in event))
            /
            ((1 - self._epsilon) * sum(self._prob[w] for w in event)
             + self._epsilon)
            )

def subsets(set_):
    """Return iterator to all subsets of an event.

    >>> [list(subset) for subset in subsets(set([2,4,5]))]
    [[], [2], [4], [5], [2, 4], [2, 5], [4, 5], [2, 4, 5]]
    """
    for subset_size in range(len(set_) + 1):
        for subset in itertools.combinations(set_, subset_size):
            yield frozenset(subset)

def mobius_inverse(map_, set_):
    """Calculate the mobius inverse of a mapping.

    >>> map_ = {}
    >>> map_[frozenset()] = 0.0
    >>> map_[frozenset([0])] = 0.25
    >>> map_[frozenset([1])] = 0.25
    >>> map_[frozenset([0,1])] = 1.0
    >>> map_inv = mobius_inverse(map_, [0,1])
    >>> map_inv[frozenset()]
    0.0
    >>> map_inv[frozenset([0])]
    0.25
    >>> map_inv[frozenset([1])]
    0.25
    >>> map_inv[frozenset([0,1])]
    0.5
    """
    inv_map = {}
    for event in subsets(set_):
        inv_map[event] = sum(
            ((-1) ** len(event - subevent)) * map_[subevent]
            for subevent in subsets(event))
    return inv_map

class BeliefFunction(LowPrev):
    def __init__(self, mass=None, lowprob=None, pspace=None):
        self._pspace = _make_tuple(pspace)
        self._mass = {}
        set_ = set(self.pspace)
        if mass:
            for event in subsets(set_):
                self._mass[event] = mass[event]
        elif lowprob:
            self._mass = mobius_inverse(lowprob, set_)
        else:
            raise ValueError("must specify mass or lowprob")
        self._matrix = None

    def get_lower(self, gamble, event=None):
        """Get lower prevision.

        >>> lowprob = {}
        >>> lowprob[frozenset()] = 0.0
        >>> lowprob[frozenset([0])] = 0.3
        >>> lowprob[frozenset([1])] = 0.2
        >>> lowprob[frozenset([0,1])] = 1.0
        >>> lpr = BeliefFunction(lowprob=lowprob, pspace=2)
        >>> print(lpr.get_lower([1,0]))
        0.3
        >>> print(lpr.get_lower([0,1]))
        0.2
        >>> print(lpr.get_lower([4,9])) # 0.8 * 4 + 0.2 * 9
        5.0
        >>> print(lpr.get_lower([5,1])) # 0.3 * 5 + 0.7 * 1
        2.2
        """
        if event is not None:
            raise NotImplementedError
        return sum(
            (self._mass[event_] * min(gamble[w] for w in event_)
             for event_ in subsets(set(self.pspace))
             if event_),
            0)

