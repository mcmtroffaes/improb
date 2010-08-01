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

import pycddlib
import random
import scipy.optimize

from improb.lowprev import LowPrev

class LowPoly(LowPrev):
    """Implements arbitrary finitely generated
    lower previsions. These are implemented as a finite sequence of
    half-spaces, each of which constrains the convex set of
    probability mass functions. Each half-space is represented by a
    gamble, and a number (i.e. its lower expectation/prevision).
    """

    def __init__(self, pspace=None, mapping=None):
        """Construct a lower prevision on *pspace*.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        """
        self._pspace = PSpace.make(pspace)
        self._matrix = None
        self._mapping = {}
        if mapping is not None:
            for key, value in mapping.iteritems():
                self._mapping[self._make_key(key)] = self._make_value(value)
        self._matrix = self._make_matrix()

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
        # clear matrix cache
        self._matrix = None

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
        # implementation detail: this is cached; set _matrix to None whenever
        # cache needs to be cleared
        if self._matrix is None:
            self._matrix = self._make_matrix()
        return self._matrix

    def _make_matrix(self):
        """Construct pycddlib matrix representation."""
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
        matrix = pycddlib.Matrix(constraints)
        matrix.lin_set = lin_set
        matrix.rep_type = pycddlib.RepType.INEQUALITY
        return matrix

    @property
    def pspace(self):
        return self._pspace

    def set_lower(self, gamble, lprev, event=None):
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

    def set_upper(self, gamble, uprev, event=None):
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

    def set_precise(self, gamble, prev, event=None):
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

    def get_lower(self, gamble, event=None):
        """Return the lower expectation for *gamble* conditional on
        *event* via natural extension.

        :param gamble: The gamble whose lower expectation to find.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The lower bound for this expectation, i.e. the natural extension of the gamble.
        :rtype: ``float``
        """
        gamble = Gamble.make(self.pspace, gamble)
        event = Event.make(self.pspace, event)
        if event == Event.make(self.pspace, self.pspace):
            matrix = self.matrix
            matrix.obj_type = pycddlib.LPObjType.MIN
            matrix.obj_func = [0] + gamble.values()
            #print(matrix) # DEBUG
            linprog = pycddlib.LinProg(matrix)
            linprog.solve()
            #print(linprog) # DEBUG
            if linprog.status == pycddlib.LPStatusType.OPTIMAL:
                return linprog.obj_value
            elif linprog.status == pycddlib.LPStatusType.INCONSISTENT:
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
            frac_result = Fraction.from_float(result).limit_denominator()
            if self.get_lower((gamble - frac_result) * event) == 0:
                return frac_result
            else:
                return result

    def get_credal_set(self):
        """Return extreme points of the credal set.

        :return: The extreme points.
        :rtype: Yields a :class:`tuple` for each extreme point.
        """
        poly = pycddlib.Polyhedron(self.matrix)
        for vert in poly.get_generators():
            yield vert[1:]

    @classmethod
    def make_random(cls, pspace=None, division=None, zero=True):
        """Generate a random coherent lower probability."""
        # for now this is just a pretty dumb method
        pspace = PSpace.make(pspace)
        while True:
            lpr = LowPrev(pspace)
            for event in pspace.subsets():
                if len(event) == 0:
                    continue
                if len(event) == len(pspace):
                    continue
                gamble = event.indicator()
                if division is None:
                    # a number between 0 and sum(event) / len(pspace)
                    while True:
                        try:
                            lpr.set_lower(gamble,
                                          random.random() * len(event) / len(pspace))
                        except ZeroDivisionError:
                            break
                else:
                    # a number between 0 and sum(event) / len(pspace)
                    # but discretized
                    lpr.set_lower(gamble,
                                  Fraction(
                                      random.randint(
                                          0 if zero else 1,
                                          (division * len(event))
                                          // len(pspace)),
                                      division))
            if lpr.is_avoiding_sure_loss():
               return lpr

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
