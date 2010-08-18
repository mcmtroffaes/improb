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

"""Polyhedral lower previsions."""

from __future__ import division, absolute_import, print_function

import cdd
import collections
from fractions import Fraction
import itertools
import scipy.optimize

from improb import PSpace, Gamble, Event
from improb.lowprev import LowPrev
from improb.setfunction import SetFunction

class LowPoly(LowPrev):
    """An arbitrary finitely generated lower prevision, that is, a
    finite intersection of half-spaces, each of which constrains the
    set of probability mass functions.

    This class is derived from :class:`collections.MutableMapping`:
    keys are (gamble, event) pairs, values are (lprev, uprev) pairs:

    >>> lpr = LowPoly(pspace='abcd', number_type='fraction')
    >>> lpr[{'a': 2, 'b': 3}, 'abcd'] = ('1.5', '1.9')
    >>> lpr[{'c': 1, 'd': 8}, 'cd'] = ('1.2', None)
    >>> print(lpr) # doctest: +NORMALIZE_WHITESPACE
    a b c d
    2 3 0 0 | a b c d : [3/2  , 19/10]
    0 0 1 8 |     c d : [6/5  ,      ]

    Instead of working on the mapping directly, you can use the
    convenience methods :meth:`set_lower`, :meth:`set_upper`, and
    :meth:`set_precise`:

    >>> lpr = LowPoly(pspace='abcd', number_type='fraction')
    >>> lpr.set_lower({'a': 2, 'b': 3}, '1.5')
    >>> lpr.set_upper({'a': 2, 'b': 3}, '1.9')
    >>> lpr.set_lower({'c': 1, 'd': 8}, '1.2', event='cd')
    >>> print(lpr) # doctest: +NORMALIZE_WHITESPACE
    a b c d
    2 3 0 0 | a b c d : [3/2  , 19/10]
    0 0 1 8 |     c d : [6/5  ,      ]
    """
    def __init__(self, pspace=None, mapping=None,
                 lprev=None, uprev=None, prev=None,
                 lprob=None, uprob=None, prob=None,
                 bba=None, number_type=None):
        """Construct a polyhedral lower prevision on *pspace*.

        Generally, you can pass a :class:`dict` as a keyword argument
        in order to initialize the lower and upper previsions and/or
        probabilities:

        >>> print(LowPoly(pspace=3, mapping={
        ...     ((3, 1, 2), True): ('1.5', None),
        ...     ((1, 0, -1), (1, 2)): ('0.25', '0.3')},
        ...     number_type='float')) # doctest: +NORMALIZE_WHITESPACE
         0    1   2
        3.0  1.0 2.0  | 0 1 2 : [1.5 ,     ]
        1.0  0.0 -1.0 |   1 2 : [0.25, 0.3 ]
        >>> print(LowPoly(pspace=3,
        ...     lprev={(1, 3, 2): '1.5', (2, 0, -1): '1'},
        ...     uprev={(2, 0, -1): '1.9'},
        ...     prev={(9, 8, 20): '15'},
        ...     lprob={(1, 2): '0.2', (1,): '0.1'},
        ...     uprob={(1, 2): '0.3', (0,): '0.9'},
        ...     prob={(2,): '0.3'},
        ...     number_type='float')) # doctest: +NORMALIZE_WHITESPACE
          0    1   2
         0.0  0.0 1.0  | 0 1 2 : [0.3 , 0.3 ]
         0.0  1.0 0.0  | 0 1 2 : [0.1 ,     ]
         0.0  1.0 1.0  | 0 1 2 : [0.2 , 0.3 ]
         1.0  0.0 0.0  | 0 1 2 : [    , 0.9 ]
         1.0  3.0 2.0  | 0 1 2 : [1.5 ,     ]
         2.0  0.0 -1.0 | 0 1 2 : [1.0 , 1.9 ]
         9.0  8.0 20.0 | 0 1 2 : [15.0, 15.0]

        As a special case, for lower/upper/precise probabilities, if
        you need to set values on singletons, you can use a list
        instead of a dictionary:

        >>> print(LowPoly(pspace='abc', lprob=['0.1', '0.2', '0.3'], number_type='fraction')) # doctest: +NORMALIZE_WHITESPACE
        a b c
        0 0 1 | a b c : [3/10, ]
        0 1 0 | a b c : [1/5 , ]
        1 0 0 | a b c : [1/10, ]

        If the first argument is a :class:`LowPoly` instance, then it
        is copied. For example:

        >>> from improb.lowprev.lowprob import LowProb
        >>> lpr = LowPoly(pspace='abc', lprob=['0.1', '0.1', '0.1'], number_type='fraction')
        >>> print(lpr)
        a b c
        0 0 1 | a b c : [1/10,     ]
        0 1 0 | a b c : [1/10,     ]
        1 0 0 | a b c : [1/10,     ]
        >>> lprob = LowProb(lpr)
        >>> print(lprob)
        a     : 1/10
          b   : 1/10
            c : 1/10

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param mapping: Mapping from (gamble, event) to (lower prevision, upper prevision).
        :type mapping: :class:`collections.Mapping`
        :param lprev: Mapping from gamble to lower prevision.
        :type lprev: :class:`collections.Mapping`
        :param uprev: Mapping from gamble to upper prevision.
        :type uprev: :class:`collections.Mapping`
        :param prev: Mapping from gamble to precise prevision.
        :type prev: :class:`collections.Mapping`
        :param lprob: Mapping from event to lower probability.
        :type lprob: :class:`collections.Mapping` or :class:`collections.Sequence`
        :param uprob: Mapping from event to upper probability.
        :type uprob: :class:`collections.Mapping` or :class:`collections.Sequence`
        :param prob: Mapping from event to precise probability.
        :type prob: :class:`collections.Mapping` or :class:`collections.Sequence`
        :param bba: Mapping from event to basic belief assignment (useful for constructing belief functions).
        :type bba: :class:`collections.Mapping`
        :param number_type: The number type.
        :type number_type: :class:`str`
        """

        def iter_items(obj):
            """Return an iterator over all items of the mapping or the
            sequence.
            """
            if isinstance(obj, collections.Mapping):
                return obj.iteritems()
            elif isinstance(obj, collections.Sequence):
                if len(obj) < len(self.pspace):
                    raise ValueError('sequence too short')
                return (((omega,), value)
                        for omega, value in itertools.izip(self.pspace, obj))
            else:
                raise TypeError(
                    'expected collections.Mapping or collections.Sequence')

        # if first argument is a LowPoly, then override all other arguments
        if isinstance(pspace, LowPoly):
            mapping = dict(pspace.iteritems())
            number_type = pspace.number_type
            pspace = pspace.pspace
        # initialize everything
        cdd.NumberTypeable.__init__(self, number_type)
        self._pspace = PSpace.make(pspace)
        self._mapping = {}
        if mapping:
            for key, value in mapping.iteritems():
                self[key] = value
        if lprev:
            for gamble, value in lprev.iteritems():
                self.set_lower(gamble, value)
        if uprev:
            for gamble, value in uprev.iteritems():
                self.set_upper(gamble, value)
        if prev:
            for gamble, value in prev.iteritems():
                self.set_precise(gamble, value)
        if lprob:
            for event, value in iter_items(lprob):
                event = self.pspace.make_event(event)
                self.set_lower(event, value)
        if uprob:
            for event, value in iter_items(uprob):
                event = self.pspace.make_event(event)
                self.set_upper(event, value)
        if prob:
            for event, value in iter_items(prob):
                event = self.pspace.make_event(event)
                self.set_precise(event, value)
        if bba:
            setfunc = SetFunction(
                pspace=self.pspace,
                data=bba,
                number_type=self.number_type)
            for event in self.pspace.subsets():
                self.set_lower(event, setfunc.get_zeta(event))

    def __len__(self):
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)

    def __contains__(self, key):
        return self._make_key(key) in self._mapping

    def __getitem__(self, key):
        return self._mapping[self._make_key(key)]

    def __setitem__(self, key, value):
        self._mapping[self._make_key(key)] = self._make_value(value)
        self._clear_cache()

    def __delitem__(self, key):
        del self._mapping[self._make_key(key)]
        self._clear_cache()

    def __str__(self):
        maxlen_pspace = max(len(str(omega)) for omega in self.pspace)
        maxlen_value = max(max(len(self.number_str(gamble[omega]))
                               for omega in self.pspace)
                           for gamble, event in self)
        maxlen = max(maxlen_pspace, maxlen_value)
        maxlen_prev = max(max(len(self.number_str(prev))
                              for prev in prevs if prev is not None)
                           for prevs in self.itervalues())
        result = " ".join("{0: ^{1}}".format(omega, maxlen)
                          for omega in self.pspace) + "\n"
        result += "\n".join(
            " ".join("{0:{1}}".format(self.number_str(value), maxlen)
                     for value in gamble.values())
            + " | "
            + " ".join("{0:{1}}".format(omega if omega in event else '',
                                        maxlen_pspace)
                       for omega in self.pspace)
            + " : ["
            + ("{0:{1}}".format(self.number_str(lprev), maxlen_prev)
               if lprev is not None else ' ' * maxlen_prev)
            + ", "
            + ("{0:{1}}".format(self.number_str(uprev), maxlen_prev)
               if uprev is not None else ' ' * maxlen_prev)
            + "]"
            for (gamble, event), (lprev, uprev)
            in sorted(self.iteritems(),
                      key=lambda val: (
                          tuple(-x for x in val[0][1].indicator(number_type='fraction').values())
                          + tuple(x for x in val[0][0].values()))))
        return result

    @property
    def matrix(self):
        """Matrix representing all the constraints of this lower prevision."""
        # implementation detail: this is cached; delete _matrix whenever
        # cache needs to be cleared
        try:
            return self._matrix
        except AttributeError:
            self._matrix = self._make_matrix()
            return self._matrix

    def _get_relevant_items(self, event=True, items=None):
        """Helper function for get_relevant_items."""
        # start with all items
        if items is None:
            items = set(self.iteritems())
        if not items:
            # special case: no items!
            return []
        compl_event = self.pspace.make_event(event).complement()
        # construct set of all conditioning events
        # (we need a variable tau_i for each of these)
        evs = set(ev for (gamble, ev), (lprev, uprev) in items)
        num_evs = len(evs)
        # construct lists of lower and upper assessments
        # (we need a variable lambda_i for each of these)
        low_items = [((gamble, ev), (lprev, uprev))
                     for (gamble, ev), (lprev, uprev) in items
                     if lprev is not None]
        upp_items = [((gamble, ev), (lprev, uprev))
                     for (gamble, ev), (lprev, uprev) in items
                     if uprev is not None]
        num_items = len(low_items + upp_items)
        # construct the linear program
        matrix = cdd.Matrix(
            # tau_i >= 0
            [([0]
              + [(1 if i == j else 0) for i in xrange(num_evs)]
              + [0 for i in xrange(num_items)])
             for j in xrange(num_evs)]
            +
            # tau_i <= 1
            [([1]
              + [(-1 if i == j else 0) for i in xrange(num_evs)]
              + [0 for i in xrange(num_items)])
             for j in xrange(num_evs)]
            +
            # lambda_i >= 0
            [([0]
              + [0 for i in xrange(num_evs)]
              + [(1 if i == j else 0) for i in xrange(num_items)])
             for j in xrange(num_items)]
            +
            # sum_{i,j,k}
            #  - tau_k ev_k[omega]
            #  - lambda_i (gamble_i[omega] - lprev_i)
            #  - lambda_j (uprev_j - gamble_j[omega]) >= 0
            [([0]
              + [-1 if (omega in ev) else 0 for ev in evs]
              + [(lprev - gamble[omega]) if omega in ev else 0
                 for (gamble, ev), (lprev, uprev) in low_items]
              + [(gamble[omega] - uprev) if omega in ev else 0
                 for (gamble, ev), (lprev, uprev) in upp_items]
              )
              for omega in compl_event],
            number_type=self.number_type)
        matrix.rep_type = cdd.RepType.INEQUALITY
        matrix.obj_type = cdd.LPObjType.MAX
        # sum over all tau_i
        matrix.obj_func = [0] + [1] * num_evs + [0] * num_items
        #print(matrix) # DEBUG
        linprog = cdd.LinProg(matrix)
        linprog.solve()
        #print(linprog.primal_solution) # DEBUG
        if linprog.status != cdd.LPStatusType.OPTIMAL:
            raise RuntimeError("BUG: unexpected status (%i)" % linprog.status)
        # calculate set of events for which tau is 1
        new_evs = set()
        for tau, ev in itertools.izip(
            linprog.primal_solution[:num_evs], evs):
            if self.number_cmp(tau, 1) == 0:
                new_evs.add(ev)
            elif self.number_cmp(tau) != 0:
                raise RuntimeError("unexpected solution for tau: {0}".format(tau))
        # derive new set of items
        new_items = set(
            ((gamble, ev), (lprev, uprev))
            for (gamble, ev), (lprev, uprev) in items
            if ev in new_evs)
        if items == new_items:
            # if all tau were 1, we are done
            return items
        else:
            # otherwise, reiterate the algorithm with the reduced set
            # of items
            return self._get_relevant_items(event=event, items=new_items)

    def get_relevant_items(self, event=True):
        """Calculate the relevant items for calculating the natural
        extension conditional on an event.

        This is part (a) (b) (c) of Algorithm 4 of Walley, Pelessoni,
        and Vicig (2004). Also see their Algorithm 2, which is a
        special case of Algorithm 4 but with event equal to the empty
        set.
        """
        # implementation detail: this is cached; delete
        # _relevant_items whenever cache needs to be cleared
        event = self.pspace.make_event(event)
        try:
            return self._relevant_items[event]
        except AttributeError:
            self._relevant_items = {}
        except KeyError:
            pass
        relevant_items = self._get_relevant_items(event=event)
        self._relevant_items[event] = relevant_items
        return relevant_items

    def _make_key(self, key):
        """Helper function to construct a key for the internal
        mapping. This implementation returns a gamble/event pair.
        Derived classes can implement additional checks, but should
        still return a gamble/event pair.
        """
        gamble, event = key
        return self.make_gamble(gamble), self.pspace.make_event(event)

    def _make_value(self, value):
        """Helper function to construct a value for the internal mapping.
        This implementation returns any lower/upper prevision pair.
        """
        lprev, uprev = value
        return (
            self.make_number(lprev) if lprev is not None else None,
            self.make_number(uprev) if uprev is not None else None)

    def _make_matrix(self):
        """Construct cdd matrix representation."""
        constraints = []
        lin_set = set()

        def add_constraint(constraint, linear=False):
            if linear:
                lin_set.add(len(constraints))
            constraints.append(constraint)

        # probabilities sum to one
        add_constraint([+1] + [-1] * len(self.pspace), linear=True)
        # probabilities are positive
        for j in self.pspace:
            add_constraint([0] + [1 if i == j else 0 for i in self.pspace])
        # add constraints on conditional expectation
        for gamble, event in self:
            lprev, uprev = self[gamble, event]
            if lprev is None and uprev is None:
                # nothing assigned
                continue
            elif lprev == uprev:
                # precise assignment
                add_constraint(
                    [0] + [value - lprev if omega in event else 0
                           for omega, value in gamble.iteritems()],
                    linear=True)
            else:
                # interval assignment
                if lprev is not None:
                    add_constraint(
                        [0] + [value - lprev if omega in event else 0
                               for omega, value in gamble.iteritems()])
                if uprev is not None:
                    add_constraint(
                        [0] + [uprev - value if omega in event else 0
                               for omega, value in gamble.iteritems()])
        # create matrix
        matrix = cdd.Matrix(constraints, number_type=self.number_type)
        matrix.lin_set = lin_set
        matrix.rep_type = cdd.RepType.INEQUALITY
        return matrix

    def _clear_cache(self):
        # clear matrix cache
        try:
            del self._matrix
        except AttributeError:
            pass
        try:
            del self._relevant_items
        except AttributeError:
            pass

    @property
    def pspace(self):
        return self._pspace

    def set_lower(self, gamble, lprev, event=True):
        """Constrain the expectation of *gamble* to be at least *lprev*.

        :param gamble: The gamble whose expectation to bound.
        :type gamble: |gambletype|
        :param lprev: The lower bound for this expectation.
        :type lprev: |numbertype|
        """
        # check that something is specified
        if lprev is None:
            return
        # update the key value
        key = self._make_key((gamble, event))
        try:
            old_lprev, uprev = self[key]
        except KeyError:
            # not yet defined, leave uprev unspecified
            uprev = None
        else:
            # already defined: constrain interval further
            lprev = (max(lprev, old_lprev)
                     if old_lprev is not None else lprev)
        self[key] = lprev, uprev

    def set_upper(self, gamble, uprev, event=True):
        """Constrain the expectation of *gamble* to be at most *uprev*.

        :param gamble: The gamble whose expectation to bound.
        :type gamble: |gambletype|
        :param uprev: The upper bound for this expectation.
        :type uprev: |numbertype|
        """
        # check that something is specified
        if uprev is None:
            return
        # update the key value
        key = self._make_key((gamble, event))
        try:
            lprev, old_uprev = self[key]
        except KeyError:
            # not yet defined, leave lprev unspecified
            lprev = None
        else:
            # already defined: constrain interval further
            uprev = (min(uprev, old_uprev)
                     if old_uprev is not None else uprev)
        self[key] = lprev, uprev

    def set_precise(self, gamble, prev, event=True):
        """Constrain the expectation of *gamble* to be exactly *prev*.

        :param gamble: The gamble whose expectation to bound.
        :type gamble: |gambletype|
        :param prev: The precise bound for this expectation.
        :type prev: |numbertype|
        """
        # check that something is specified
        if prev is None:
            return
        # update the key value
        key = self._make_key((gamble, event))
        try:
            old_lprev, old_uprev = self[key]
        except KeyError:
            # not yet defined, copy as is
            lprev = prev
            uprev = prev
        else:
            # already defined: constrain interval further
            lprev = (max(prev, old_lprev)
                     if old_lprev is not None else prev)
            uprev = (min(prev, old_uprev)
                     if old_uprev is not None else prev)
        self[key] = lprev, uprev

    def get_lower(self, gamble, event=True, algorithm='linprog'):
        """Calculate lower expectation, using linear programming."""
        # set fastest algorithm
        if algorithm is None:
            algorithm = 'linprog'
        # check algorithm
        if algorithm != 'linprog':
            raise ValueError("invalid algorithm '{0}'".format(algorithm))
        # calculate lower expectation
        gamble = self.make_gamble(gamble)
        event = self.pspace.make_event(event)
        if event == self.pspace.make_event(True):
            matrix = self.matrix
            matrix.obj_type = cdd.LPObjType.MIN
            matrix.obj_func = [0] + gamble.values()
            #print(matrix) # DEBUG
            linprog = cdd.LinProg(matrix)
            linprog.solve()
            #print(linprog) # DEBUG
            if linprog.status == cdd.LPStatusType.OPTIMAL:
                return linprog.obj_value
            elif linprog.status == cdd.LPStatusType.INCONSISTENT:
                raise ValueError("lower prevision incurs sure loss")
            else:
                raise RuntimeError("BUG: unexpected status (%i)" % linprog.status)
        else:
            a = min(gamble[omega] for omega in event)
            b = max(gamble[omega] for omega in event)
            if a == b:
                # constant gamble, can only have this conditional prevision
                # (also, scipy.optimize.brentq raises an exception if a == b)
                return a
            lowprev_event = self.get_lower(event.indicator(self.number_type),
                                           algorithm=algorithm)
            if lowprev_event == 0:
                raise ZeroDivisionError(
                    "cannot condition on event with zero lower probability")
            try:
                result = scipy.optimize.brentq(
                    f=lambda mu: float(self.get_lower((gamble - mu) * event,
                                                      algorithm=algorithm)),
                    a=float(a), b=float(b))
            except ValueError as exc:
                # re-raise with more detail
                raise ValueError("{0}\n{1}\n{2}\n{3} {4}".format(
                    exc,
                    gamble, event,
                    self.get_lower((gamble - a) * event, algorithm=algorithm), 
                    self.get_lower((gamble - b) * event, algorithm=algorithm)))
            # see if we can get the exact fractional solution
            if self.number_type == 'fraction':
                frac_result = Fraction.from_float(result).limit_denominator()
                if self.get_lower((gamble - frac_result) * event,
                                  algorithm=algorithm) == 0:
                    return frac_result
            return result

    def get_credal_set(self):
        """Return extreme points of the credal set.

        :return: The extreme points.
        :rtype: Yields a :class:`tuple` for each extreme point.
        """
        poly = cdd.Polyhedron(self.matrix)
        for vert in poly.get_generators():
            yield vert[1:]

    def get_coherent(self, algorithm='linprog'):
        """Return a coherent version, using linear programming."""
        if not self.is_avoiding_sure_loss():
            raise ValueError('incurs sure loss')
        # copy the assignments
        mapping = dict(self.iteritems())
        # note: we wrap iteritems in a list because we're changing the
        # mapping as we iterate
        for (gamble, event), (lprev, uprev) in list(mapping.iteritems()):
            # fix lower and upper previsions
            if lprev is not None:
                lprev = self.get_lower(gamble, event, algorithm=algorithm)
            if uprev is not None:
                uprev = self.get_upper(gamble, event, algorithm=algorithm)
            mapping[gamble, event] = lprev, uprev
        # create new lower prevision (of the same class)
        return self.__class__(
            pspace=self.pspace,
            mapping=mapping,
            number_type=self.number_type)

    def extend(self, keys=None, lower=True, upper=True, algorithm='linprog'):
        """Calculate coherent extension to the given keys
        (gamble/event pairs), using linear programming.

        :param keys: The gamble/event pairs to extend. If :const:`None`, then
            extends to the full domain (for
            :class:`~improb.lowprev.lowpoly.LowPoly` this raises a
            :exc:`~exceptions.ValueError`, however some derived
            classes implement this if they have a finite domain).
        :type keys: :class:`collections.Iterable`
        :param lower: Whether to extend the lower bounds.
        :type lower: :class:`bool`
        :param upper: Whether to extend the upper bounds.
        :type upper: :class:`bool`

        >>> pspace = PSpace('xyz')
        >>> lpr = LowPoly(pspace=pspace, lprob=['0.1', '0.2', '0.15'], number_type='fraction')
        >>> print(lpr)
        x y z
        0 0 1 | x y z : [3/20,     ]
        0 1 0 | x y z : [1/5 ,     ]
        1 0 0 | x y z : [1/10,     ]
        >>> for event in pspace.subsets(empty=False):
        ...     lpr.extend((subevent, event) for subevent in pspace.subsets(event))
        >>> print(lpr)
        x y z
        0 0 0 | x y z : [0    , 0    ]
        0 0 1 | x y z : [3/20 , 7/10 ]
        0 1 0 | x y z : [1/5  , 3/4  ]
        0 1 1 | x y z : [7/20 , 9/10 ]
        1 0 0 | x y z : [1/10 , 13/20]
        1 0 1 | x y z : [1/4  , 4/5  ]
        1 1 0 | x y z : [3/10 , 17/20]
        1 1 1 | x y z : [1    , 1    ]
        0 0 0 | x y   : [0    , 0    ]
        0 1 0 | x y   : [4/17 , 15/17]
        1 0 0 | x y   : [2/17 , 13/17]
        1 1 0 | x y   : [1    , 1    ]
        0 0 0 | x   z : [0    , 0    ]
        0 0 1 | x   z : [3/16 , 7/8  ]
        1 0 0 | x   z : [1/8  , 13/16]
        1 0 1 | x   z : [1    , 1    ]
        0 0 0 | x     : [0    , 0    ]
        1 0 0 | x     : [1    , 1    ]
        0 0 0 |   y z : [0    , 0    ]
        0 0 1 |   y z : [1/6  , 7/9  ]
        0 1 0 |   y z : [2/9  , 5/6  ]
        0 1 1 |   y z : [1    , 1    ]
        0 0 0 |   y   : [0    , 0    ]
        0 1 0 |   y   : [1    , 1    ]
        0 0 0 |     z : [0    , 0    ]
        0 0 1 |     z : [1    , 1    ]
        """
        if keys is None:
            raise ValueError(
                'cannot extend to full domain: specify keys')
        for gamble, event in keys:
            try:
                lprev, uprev = self[gamble, event]
            except KeyError:
                lprev, uprev = None, None
            if lower:
                lprev = self.get_lower(gamble, event, algorithm)
            if upper:
                uprev = self.get_upper(gamble, event, algorithm)
            self[gamble, event] = lprev, uprev

    def is_avoiding_sure_loss(self, algorithm='linprog'):
        """Check avoiding sure loss by linear programming.

        This is Algorithm 2 of Walley, Pelessoni, and Vicig (2004).
        """
        # if there are no relevant items for conditioning on the empty
        # set, then we avoids sure loss
        return not self.get_relevant_items(event=False)

    def is_coherent(self, algorithm='linprog'):
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss(algorithm):
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, event in self:
            lprev, uprev = self[gamble, event]
            if (lprev is not None
                and self.number_cmp(
                    self.get_lower(gamble, event, algorithm), lprev) == 1):
                return False
            if (uprev is not None
                and self.number_cmp(
                    self.get_upper(gamble, event, algorithm), uprev) == -1):
                return False
        return True

    def is_linear(self, algorithm='linprog'):
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss(algorithm):
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, event in self:
            if self.number_cmp(
                self.get_lower(gamble, event, algorithm),
                self.get_upper(gamble, event, algorithm)) != 0:
                return False
        return True

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
