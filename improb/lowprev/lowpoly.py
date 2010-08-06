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

    This class is derived from :class:`collections.Mapping`: keys are
    (gamble, event) pairs, values are (lprev, uprev) pairs. Instead of
    working on the mapping directly, you can use the convenience
    methods :meth:`set_lower`, :meth:`set_upper`, and
    :meth:`set_precise`.
    """
    def __init__(self, pspace=None, mapping=None,
                 lprev=None, uprev=None, prev=None,
                 lprob=None, uprob=None, prob=None,
                 bba=None, number_type='float'):
        """Construct a lower prevision on *pspace*.

        Generally, you can pass a :class:`dict` as a keyword argument
        in order to initialize the lower and upper previsions and/or
        probabilities:

        >>> print(LowPoly(3, mapping={
        ...     ((3, 1, 2), True): ('1.5', None),
        ...     ((1, 0, -1), (1, 2)): ('0.25', '0.3')})
        ...     ) # doctest: +NORMALIZE_WHITESPACE
          0      1      2
         1.000  0.000 -1.000 |   1 2 : [0.250, 0.300]
         3.000  1.000  2.000 | 0 1 2 : [1.500,      ]
        >>> print(LowPoly(3,
        ...     lprev={(1, 3, 2): '1.5', (2, 0, -1): '1'},
        ...     uprev={(2, 0, -1): '1.9'},
        ...     prev={(9, 8, 20): '15'},
        ...     lprob={(1, 2): '0.2', (1,): '0.1'},
        ...     uprob={(1, 2): '0.3', (0,): '0.9'},
        ...     prob={(2,): '0.3'},
        ...     )) # doctest: +NORMALIZE_WHITESPACE
          0      1      2
         0.000  0.000  1.000 | 0 1 2 : [ 0.300,  0.300]
         0.000  1.000  0.000 | 0 1 2 : [ 0.100,       ]
         0.000  1.000  1.000 | 0 1 2 : [ 0.200,  0.300]
         1.000  0.000  0.000 | 0 1 2 : [      ,  0.900]
         1.000  3.000  2.000 | 0 1 2 : [ 1.500,       ]
         2.000  0.000 -1.000 | 0 1 2 : [ 1.000,  1.900]
         9.000  8.000 20.000 | 0 1 2 : [15.000, 15.000]

        As a special case, for lower/upper/precise probabilities, if
        you need to set values on singletons, you can use a list
        instead of a dictionary:

        >>> print(LowPoly(3, lprob=['0.1', '0.2', '0.3'])) # doctest: +NORMALIZE_WHITESPACE
         0      1      2
        0.000  0.000  1.000 | 0 1 2 : [0.300, ]
        0.000  1.000  0.000 | 0 1 2 : [0.200, ]
        1.000  0.000  0.000 | 0 1 2 : [0.100, ]

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
        :type bba: :class:`collections.Mapping` or :class:`collections.Sequence`
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
            setfunc = SetFunction(self.pspace, bba, self.number_type)
            for event, value in setfunc.get_mobius_inverse():
                self.set_lower(event, value)

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
        maxlen_value = max(max(len("{0:.3f}".format(float(gamble[omega])))
                               for omega in self.pspace)
                           for gamble, event in self)
        maxlen = max(maxlen_pspace, maxlen_value)
        maxlen_prev = max(max(len("{0:.3f}".format(float(prev)))
                              for prev in prevs if prev is not None)
                           for prevs in self.itervalues())
        result = " ".join("{0: ^{1}}".format(omega, maxlen)
                          for omega in self.pspace) + "\n"
        result += "\n".join(
            " ".join("{0:{1}.3f}".format(float(value), maxlen)
                     for value in gamble.values())
            + " | "
            + " ".join("{0:{1}}".format(omega if omega in event else '',
                                        maxlen_pspace)
                       for omega in self.pspace)
            + " : ["
            + ("{0:{1}.3f}".format(float(lprev), maxlen_prev)
               if lprev is not None else ' ' * maxlen_prev)
            + ", "
            + ("{0:{1}.3f}".format(float(uprev), maxlen_prev)
               if uprev is not None else ' ' * maxlen_prev)
            + "]"
            for (gamble, event), (lprev, uprev)
            in sorted(self.iteritems(),
                      key=lambda val: tuple(x for x in val[0][0].values())))
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
        matrix.data.lin_set = lin_set
        matrix.data.rep_type = cdd.RepType.INEQUALITY
        return matrix

    def _clear_cache(self):
        # clear matrix cache
        try:
            del self._matrix
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

    def get_lower(self, gamble, event=True):
        """Return the lower expectation for *gamble* conditional on
        *event* via natural extension.

        :param gamble: The gamble whose lower expectation to find.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The lower bound for this expectation, i.e. the natural extension of the gamble.
        :rtype: ``float``
        """
        gamble = self.make_gamble(gamble)
        event = self.pspace.make_event(event)
        if event == self.pspace.make_event(True):
            matrix = self.matrix
            matrix.data.obj_type = cdd.LPObjType.MIN
            matrix.data.obj_func = [0] + gamble.values()
            #print(matrix) # DEBUG
            linprog = cdd.LinProg(matrix)
            linprog.data.solve()
            #print(linprog) # DEBUG
            if linprog.data.status == cdd.LPStatusType.OPTIMAL:
                return linprog.data.obj_value
            elif linprog.data.status == cdd.LPStatusType.INCONSISTENT:
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
            lowprev_event = self.get_lower(event)
            if lowprev_event == 0:
                raise ZeroDivisionError(
                    "cannot condition on event with zero lower probability")
            try:
                result = scipy.optimize.brentq(
                    f=lambda mu: float(self.get_lower((gamble - mu) * event)),
                    a=float(a), b=float(b))
            except ValueError as exc:
                # re-raise with more detail
                raise ValueError("{0}\n{1}\n{2}\n{3} {4}".format(
                    exc,
                    gamble, event,
                    self.get_lower((gamble - a) * event), 
                    self.get_lower((gamble - b) * event)))
            # see if we can get the exact fractional solution
            if self.number_type == 'fraction':
                frac_result = Fraction.from_float(result).limit_denominator()
                if self.get_lower((gamble - frac_result) * event) == 0:
                    return frac_result
            return result

    def get_credal_set(self):
        """Return extreme points of the credal set.

        :return: The extreme points.
        :rtype: Yields a :class:`tuple` for each extreme point.
        """
        poly = cdd.Polyhedron(self.matrix)
        for vert in poly.data.get_generators():
            yield vert[1:]

    def get_coherent(self):
        """Return a coherent version."""
        if not self.is_avoiding_sure_loss():
            raise ValueError('incurs sure loss')
        # copy the assignments
        mapping = dict(self.iteritems())
        # note: we wrap iteritems in a list because we're changing the
        # mapping as we iterate
        for (gamble, event), (lprev, uprev) in list(mapping.iteritems()):
            # fix lower and upper previsions
            if lprev is not None:
                lprev = self.get_lower(gamble, event)
            if uprev is not None:
                uprev = self.get_upper(gamble, event)
            mapping[gamble, event] = lprev, uprev
        # create new lower prevision (of the same class)
        return self.__class__(
            pspace=self.pspace,
            mapping=mapping,
            number_type=self.number_type)

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
