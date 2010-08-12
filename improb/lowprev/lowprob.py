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

"""Coherent lower probabilities."""

from __future__ import division, absolute_import, print_function

import cdd
import collections
from fractions import Fraction
import itertools
import random

from improb import PSpace, Gamble, Event
from improb.lowprev.lowpoly import LowPoly
from improb.setfunction import SetFunction

class LowProb(LowPoly):
    """An unconditional lower probability. This class is identical to
    :class:`~improb.lowprev.lowpoly.LowPoly`, except that only
    unconditional assessments on events are allowed.

    >>> print(LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2'}, number_type='float'))
    0 1   : 0.1
      1 2 : 0.2
    >>> print(LowProb(3, lprev={(3, 1, 0): 1}, number_type='float')) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: not an indicator gamble
    >>> print(LowProb(3, uprob={(0, 1): '0.1'}, number_type='float')) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: cannot specify upper prevision
    >>> print(LowProb(3, mapping={((3, 1, 0), (0, 1)): ('1.4', None)}, number_type='float')) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: not unconditional
    >>> lpr = LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2', (2,): '0.05'}, number_type='fraction')
    >>> lpr.extend()
    >>> print(lpr)
          : 0
    0     : 0
      1   : 0
        2 : 1/20
    0 1   : 1/10
    0   2 : 1/20
      1 2 : 1/5
    0 1 2 : 1
    >>> print(lpr.mobius)
          : 0
    0     : 0
      1   : 0
        2 : 1/20
    0 1   : 1/10
    0   2 : 0
      1 2 : 3/20
    0 1 2 : 7/10
    """

    def _clear_cache(self):
        LowPoly._clear_cache(self)
        try:
            del self._set_function
        except AttributeError:
            pass
        try:
            del self._mobius
        except AttributeError:
            pass

    @property
    def set_function(self):
        """The lower probability as
        :class:`~improb.setfunction.SetFunction`.
        """
        # TODO should return an immutable object

        # implementation detail: this is cached; delete
        # _set_function whenever cache needs to be cleared
        try:
            return self._set_function
        except AttributeError:
            self._set_function = self._make_set_function()
            return self._set_function

    @property
    def mobius(self):
        """The mobius transform of the assigned unconditional lower
        probabilities, as :class:`~improb.setfunction.SetFunction`.

        .. seealso::

            :meth:`improb.setfunction.SetFunction.get_mobius`
                Mobius transform calculation of an arbitrary set function.

            :class:`improb.lowprev.belfunc.BelFunc`
                Belief functions.
        """
        # TODO should return an immutable object

        # implementation detail: this is cached; delete
        # _mobius whenever cache needs to be cleared
        try:
            return self._mobius
        except AttributeError:
            self._mobius = self._make_mobius()
            return self._mobius

    @classmethod
    def make_random(cls, pspace=None, division=None, zero=True,
                    number_type='float'):
        """Generate a random coherent lower probability."""
        # for now this is just a pretty dumb method
        pspace = PSpace.make(pspace)
        lpr = cls(pspace=pspace, number_type=number_type)
        for event in pspace.subsets():
            if len(event) == 0:
                continue
            if len(event) == len(pspace):
                continue
            gamble = event.indicator(number_type=number_type)
            if division is None:
                # a number between 0 and len(event) / len(pspace)
                lprob = random.random() * len(event) / len(pspace)
            else:
                # a number between 0 and len(event) / len(pspace)
                # but discretized
                lprob = Fraction(
                    random.randint(
                        0 if zero else 1,
                        (division * len(event)) // len(pspace)),
                    division)
            # make a copy of lpr
            tmplpr = cls(pspace=pspace, mapping=lpr, number_type=number_type)
            # set new assignment, and give up if it incurs sure loss
            tmplpr.set_lower(gamble, lprob)
            if not tmplpr.is_avoiding_sure_loss():
                break
            else:
                lpr.set_lower(gamble, lprob)
        # done! return coherent version of it
        return lpr.get_coherent()

    def __str__(self):
        return str(self.set_function)

    # we override _make_key and _make_value to meet the constraints

    def _make_key(self, key):
        gamble, event = LowPoly._make_key(self, key)
        if not event.is_true():
            raise ValueError('not unconditional')
        return gamble, event

    def _make_value(self, value):
        lprev, uprev = LowPoly._make_value(self, value)
        if uprev is not None:
            raise ValueError('cannot specify upper prevision')
        return lprev, uprev

    def _make_set_function(self):
        return SetFunction(
            pspace=self.pspace,
            data=dict((self.pspace.make_event(gamble), lprev)
                      for (gamble, cond_event), (lprev, uprev) in self.iteritems()),
            number_type=self.number_type)

    def _make_mobius(self):
        """Constructs basic belief assignment corresponding to the
        assigned unconditional lower probabilities.
        """
        # construct set function corresponding to this lower probability
        return SetFunction(
            pspace=self.pspace,
            data=dict((event, self.set_function.get_mobius(event))
                      for event in self.pspace.subsets()),
            number_type=self.number_type)

    def extend(self, keys=None, lower=True, upper=True, algorithm='linprog'):
        if keys is None:
            LowPoly.extend(
                self,
                ((event, True) for event in self.pspace.subsets()),
                lower=True,
                upper=False,
                algorithm=algorithm)
        else:
            LowPoly.extend(self, keys, lower, upper, algorithm)

    def is_completely_monotone(self):
        """Checks whether the lower probability is completely monotone
        or not.

        .. warning::

           The lower probability must be defined for all events. If
           needed, call :meth:`~improb.lowprev.lowpoly.LowPoly.extend`
           first.

        >>> lpr = LowProb(
        ...     pspace='abcd',
        ...     lprob={'ab': '0.2', 'bc': '0.2', 'abc': '0.2', 'b': '0.1'},
        ...     number_type='fraction')
        >>> lpr.extend()
        >>> print(lpr)
                : 0
        a       : 0
          b     : 1/10
            c   : 0
              d : 0
        a b     : 1/5
        a   c   : 0
        a     d : 0
          b c   : 1/5
          b   d : 1/10
            c d : 0
        a b c   : 1/5
        a b   d : 1/5
        a   c d : 0
          b c d : 1/5
        a b c d : 1
        >>> print(lpr.mobius)
                : 0
        a       : 0
          b     : 1/10
            c   : 0
              d : 0
        a b     : 1/10
        a   c   : 0
        a     d : 0
          b c   : 1/10
          b   d : 0
            c d : 0
        a b c   : -1/10
        a b   d : 0
        a   c d : 0
          b c d : 0
        a b c d : 4/5
        >>> lpr.is_completely_monotone() # (it is in fact not even 2-monotone)
        False

        >>> lpr = LowProb(
        ...     pspace='abcd',
        ...     lprob={'ab': '0.2', 'bc': '0.2', 'abc': '0.3', 'b': '0.1'},
        ...     number_type='fraction')
        >>> lpr.extend()
        >>> print(lpr)
                : 0
        a       : 0
          b     : 1/10
            c   : 0
              d : 0
        a b     : 1/5
        a   c   : 0
        a     d : 0
          b c   : 1/5
          b   d : 1/10
            c d : 0
        a b c   : 3/10
        a b   d : 1/5
        a   c d : 0
          b c d : 1/5
        a b c d : 1
        >>> print(lpr.mobius)
                : 0
        a       : 0
          b     : 1/10
            c   : 0
              d : 0
        a b     : 1/10
        a   c   : 0
        a     d : 0
          b c   : 1/10
          b   d : 0
            c d : 0
        a b c   : 0
        a b   d : 0
        a   c d : 0
          b c d : 0
        a b c d : 7/10
        >>> lpr.is_completely_monotone()
        True
        """
        # it is necessary and sufficient that the Mobius transform is
        # non-negative
        for value in self.mobius.itervalues():
            if self.number_cmp(value) < 0:
                return False
        return True

    def is_n_monotone(self, monotonicity=None):
        """Given that the lower probability is (n-1)-monotone, is the
        lower probability n-monotone?

        .. note::

            To check for n-monotonicity, call this method with
            *monotonicity=xrange(n + 1)*.

        .. note::

            For convenience, 0-montonicity is defined as empty set and
            possibility space having lower probability 0 and 1
            respectively.

        .. warning::

           The lower probability must be defined for all events. If
           needed, call :meth:`~improb.lowprev.lowpoly.LowPoly.extend`
           first.

        .. warning::

            For large levels of monotonicity, it is slightly more
            efficient to call
            :meth:`~improb.setfunction.SetFunction.is_bba_n_monotone`
            on :attr:`~improb.lowprev.lowprob.LowProb.mobius`.
        """
        # check 0-monotonicity
        if monotonicity == 0:
            if self.number_cmp(self[False, True]) != 0:
                return False
            if self.number_cmp(self[True, True], 1) != 0:
                return False
        # iterate over all constraints
        for constraint in self.get_constraints_n_monotone(
            self.pspace, monotonicity):
            # check the constraint
            if self.number_cmp(
                sum(coeff * self[event, True][0]
                    for event, coeff in constraint)) < 0:
                return False
        return True

    @classmethod
    def get_constraints_n_monotone(cls, pspace, monotonicity=None):
        """Yields constraints for lower probabilities with given
        monotonicity.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param monotonicity: Requested level of monotonicity (see
            notes below for details).
        :type monotonicity: :class:`int` or
            :class:`collections.Iterable` of :class:`int`

        As described in
        :meth:`~improb.setfunction.SetFunction.get_constraints_bba_n_monotone`,
        the n-monotonicity constraints on basic belief assignment are:

        .. math::

            \sum_{B\colon C\subseteq B\subseteq A}m(B)\ge 0

        for all :math:`C\subseteq A\subseteq\Omega`, with
        :math:`1\le|C|\le n`.

        By the Mobius transform, this is equivalent to:

        .. math::

            \sum_{B\colon C\subseteq B\subseteq A}
            \sum_{D\colon D\subseteq B}(-1)^{|B\setminus D|}
            \underline{P}(D)\ge 0

        Once noted that

        .. math::

            (C\subseteq B\subseteq A\quad \& \quad D\subseteq B)
            \iff
            (C\cup D\subseteq B\subseteq A\quad \& \quad D\subseteq A),

        we can conveniently rewrite the sum as:

        .. math::

            \sum_{D\colon D\subseteq A}
            \sum_{B\colon C\cup D\subseteq B\subseteq A}(-1)^{|B\setminus D|}
            \underline{P}(D)\ge 0

        This implementation iterates over all :math:`C\subseteq
        A\subseteq\Omega`, with :math:`|C|=n`, and yields each
        constraint as an iterable of (event, coefficient) pairs, where
        zero coefficients are omitted.

        .. note::

            As just mentioned, this method returns the constraints
            corresponding to the latter equation for :math:`|C|`
            equal to *monotonicity*. To get all the
            constraints for n-monotonicity, call this method with
            *monotonicity=xrange(1, n + 1)*.

            The rationale for this approach is that, in case you
            already know that (n-1)-monotonicity is satisfied, then
            you only need the constraints for *monotonicity=n* to
            check for n-monotonicity.

        .. note::

            The trivial constraints that the empty set must have lower
            probability zero, and that the possibility space must have
            lower probability one, are not included: so for
            *monotonicity=0* this method returns an empty iterator.

        >>> pspace = PSpace("abc")
        >>> for mono in xrange(1, len(pspace) + 1):
        ...     print("{0} monotonicity:".format(mono))
        ...     print(" ".join("{0:<{1}}".format("".join(i for i in event), len(pspace))
        ...                    for event in pspace.subsets()))
        ...     constraints = [
        ...         dict(constraint) for constraint in
        ...         LowProb.get_constraints_n_monotone(pspace, mono)]
        ...     constraints = [
        ...         [constraint.get(event, 0) for event in pspace.subsets()]
        ...         for constraint in constraints]
        ...     for constraint in sorted(constraints):
        ...         print(" ".join("{0:<{1}}".format(value, len(pspace))
        ...                        for value in constraint))
        1 monotonicity:
            a   b   c   ab  ac  bc  abc
        -1  0   0   1   0   0   0   0  
        -1  0   1   0   0   0   0   0  
        -1  1   0   0   0   0   0   0  
        0   -1  0   0   0   1   0   0  
        0   -1  0   0   1   0   0   0  
        0   0   -1  0   0   0   1   0  
        0   0   -1  0   1   0   0   0  
        0   0   0   -1  0   0   1   0  
        0   0   0   -1  0   1   0   0  
        0   0   0   0   -1  0   0   1  
        0   0   0   0   0   -1  0   1  
        0   0   0   0   0   0   -1  1  
        2 monotonicity:
            a   b   c   ab  ac  bc  abc
        0   0   0   1   0   -1  -1  1  
        0   0   1   0   -1  0   -1  1  
        0   1   0   0   -1  -1  0   1  
        1   -1  -1  0   1   0   0   0  
        1   -1  0   -1  0   1   0   0  
        1   0   -1  -1  0   0   1   0  
        3 monotonicity:
            a   b   c   ab  ac  bc  abc
        -1  1   1   1   -1  -1  -1  1  
        """
        pspace = PSpace.make(pspace)
        # check type
        if monotonicity is None:
            raise ValueError("specify monotonicity")
        elif isinstance(monotonicity, collections.Iterable):
            # special case: return it for all values in the iterable
            for mono in monotonicity:
                for constraint in cls.get_constraints_n_monotone(pspace, mono):
                    yield constraint
            return
        elif not isinstance(monotonicity, (int, long)):
            raise TypeError("monotonicity must be integer")
        # check value
        if monotonicity < 0:
            raise ValueError("specify a non-negative monotonicity")
        if monotonicity == 0:
            # don't return constraints in this case
            return
        # yield all constraints
        for event_a in pspace.subsets(size=xrange(monotonicity, len(pspace) + 1)):
            for subevent_c in pspace.subsets(event_a, size=monotonicity):
                yield (
                    (subevent_d,
                     sum((-1) ** len(event_b - subevent_d)
                         for event_b in pspace.subsets(
                             event_a, contains=(subevent_d | subevent_c))))
                    for subevent_d in pspace.subsets(event_a))

    @classmethod
    def make_extreme_n_monotone(cls, pspace, monotonicity=None):
        """Yield extreme lower probabilities with given monotonicity.

        .. warning::

           Currently this doesn't work very well except for the cases
           below.

        >>> lprs = list(LowProb.make_extreme_n_monotone('abc', monotonicity=2))
        >>> len(lprs)
        8
        >>> all(lpr.is_coherent() for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(2) for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(3) for lpr in lprs)
        False
        >>> lprs = list(LowProb.make_extreme_n_monotone('abc', monotonicity=3))
        >>> len(lprs)
        7
        >>> all(lpr.is_coherent() for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(2) for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(3) for lpr in lprs)
        True
        >>> lprs = list(LowProb.make_extreme_n_monotone('abcd', monotonicity=2))
        >>> len(lprs)
        41
        >>> all(lpr.is_coherent() for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(2) for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(3) for lpr in lprs)
        False
        >>> all(lpr.is_n_monotone(4) for lpr in lprs)
        False
        >>> lprs = list(LowProb.make_extreme_n_monotone('abcd', monotonicity=3))
        >>> len(lprs)
        16
        >>> all(lpr.is_coherent() for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(2) for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(3) for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(4) for lpr in lprs)
        False
        >>> lprs = list(LowProb.make_extreme_n_monotone('abcd', monotonicity=4))
        >>> len(lprs)
        15
        >>> all(lpr.is_coherent() for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(2) for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(3) for lpr in lprs)
        True
        >>> all(lpr.is_n_monotone(4) for lpr in lprs)
        True
        >>> # cddlib hangs on larger possibility spaces
        >>> #lprs = list(LowProb.make_extreme_n_monotone('abcde', monotonicity=2))
        """
        pspace = PSpace.make(pspace)
        # constraint for empty set and full set
        matrix = cdd.Matrix(
            [[0] + [1 if event.is_false() else 0 for event in pspace.subsets()],
             [-1] + [1 if event.is_true() else 0 for event in pspace.subsets()]],
            linear=True,
            number_type='fraction')
        # constraints for monotonicity
        constraints = [
            dict(constraint) for constraint in
            cls.get_constraints_n_monotone(pspace, xrange(1, monotonicity + 1))]
        matrix.extend([[0] + [constraint.get(event, 0)
                              for event in pspace.subsets()]
                       for constraint in constraints])
        matrix.rep_type = cdd.RepType.INEQUALITY

        # debug: simplify matrix
        #print(pspace, monotonicity) # debug
        #print("original:", len(matrix))
        #matrix.canonicalize()
        #print("new     :", len(matrix))
        #print(matrix) # debug

        # calculate extreme points
        poly = cdd.Polyhedron(matrix)
        # convert these points back to lower probabilities
        #print(poly.get_generators()) # debug
        for vert in poly.get_generators():
            yield cls(
                pspace=pspace,
                lprob=dict((event, vert[1 + index])
                           for index, event in enumerate(pspace.subsets())),
                number_type='fraction')
