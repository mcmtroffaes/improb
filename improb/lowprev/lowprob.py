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
from itertools import chain, izip
from operator import itemgetter
import random

from improb import PSpace, Gamble, Event
from improb.lowprev.lowpoly import LowPoly
from improb.setfunction import SetFunction

class LowProb(LowPoly):
    """An unconditional lower probability. This class is identical to
    :class:`~improb.lowprev.lowpoly.LowPoly`, except that only
    unconditional assessments on events are allowed.

    >>> print(LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2'}))
    0 1   : 1/10
      1 2 : 1/5
    >>> print(LowProb(3, lprev={(3, 1, 0): 1})) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: not an indicator gamble
    >>> print(LowProb(3, uprob={(0, 1): '0.1'})) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: cannot specify upper prevision
    >>> print(LowProb(3, mapping={((3, 1, 0), (0, 1)): (1.4, None)})) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: not unconditional
    >>> lpr = LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2', (2,): '0.05'})
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
    >>> lpr = LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2', (2,): '0.05'})
    >>> lpr.extend([(lpr.pspace.make_event((0, 2)), True)])
    >>> print(lpr)
        2 : 1/20
    0 1   : 1/10
    0   2 : 1/20
      1 2 : 1/5
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

    def get_extend_domain(self):
        return ((event, True) for event in self.pspace.subsets())

    # lowprobs have no upper, so default to upper=False
    def extend(self, keys=None, lower=True, upper=False, algorithm='linprog'):
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
        ...     lprob={'ab': '0.2', 'bc': '0.2', 'abc': '0.2', 'b': '0.1'})
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
        ...     lprob={'ab': '0.2', 'bc': '0.2', 'abc': '0.3', 'b': '0.1'})
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

    # TODO move to LowPoly
    def _scalar(self, other, oper):
        """
        :raises: :exc:`~exceptions.TypeError` if other is not a scalar

        .. doctest::

            >>> pspace = PSpace('abc')
            >>> lprob = LowProb(pspace, 
            ...                 lprob={'a': '1/8', 'b': '1/7', 'c': '1/6'},
            ...                 number_type='fraction')
            >>> lprob.extend()
            >>> print(1-.5*lprob*1.5-.5)
                  : 1/2
            a     : 13/32
              b   : 11/28
                c : 3/8
            a b   : 67/224
            a   c : 9/32
              b c : 15/56
            a b c : -1/4
        """
        other = self.make_number(other)
        return LowProb(self.pspace,
                       lprev=dict([(gamble, oper(lprev, other))
                                   for (gamble, event), (lprev, uprev)
                                   in self.iteritems()]),
                       number_type=self.number_type)

    # TODO move to LowPoly
    def _pointwise(self, other, oper):
        """
        :raises: :exc:`~exceptions.ValueError` if possibility spaces or domain
            do not match

        .. doctest::

            >>> pspace = PSpace('abc')
            >>> lprob = LowProb(pspace,
            ...                 lprob={'a': '1/8', 'b': '1/7', 'c': '1/6'},
            ...                 number_type='fraction')
            >>> lprob.extend()
            >>> (lprob * lprob).is_coherent()
            True
            >>> print(lprob + lprob)
                  : 0
            a     : 1/4
              b   : 2/7
                c : 1/3
            a b   : 15/28
            a   c : 7/12
              b c : 13/21
            a b c : 2
            >>> print(lprob / 2)
                  : 0
            a     : 1/16
              b   : 1/14
                c : 1/12
            a b   : 15/112
            a   c : 7/48
              b c : 13/84
            a b c : 1/2
        """
        if isinstance(other, LowProb):
            if self.pspace != other.pspace:
                raise ValueError("possibility space mismatch")
            if set(self.keys()) != set(other.keys()): # order can also differ!
                raise ValueError("domain mismatch")
            if self.number_type != other.number_type:
                raise ValueError("number type mismatch")
            return LowProb(self.pspace,
                           lprev=dict([(gamble,
                                        oper(lprev, other[gamble, True][0]))
                                       for (gamble, event), (lprev, uprev)
                                       in self.iteritems()]),
                           number_type=self.number_type)
        else:
            # will raise a type error if operand is not scalar
            return self._scalar(other, oper)

    # TODO move to LowPoly
    __add__ = lambda self, other: self._pointwise(other, self.NumberType.__add__)
    __sub__ = lambda self, other: self._pointwise(other, self.NumberType.__sub__)
    __mul__ = lambda self, other: self._pointwise(other, self.NumberType.__mul__)
    __truediv__ = lambda self, other: self._scalar(other, self.NumberType.__truediv__)

    __neg__ = lambda self: self * (-1)

    __radd__ = __add__
    __rsub__ = lambda self, other: self.__sub__(other).__neg__()
    __rmul__ = __mul__

    def get_precise_part(self):
        """Extract the precise part and its relative weight.

        Every coherent lower probability :math:`\underline{P}` can be written
        as a unique convex mixture :math:`\lambda P+(1-\lambda)\underline{Q}`
        of an additive 'precise' part :math:`P` and an 'imprecise' part
        :math:`\underline{Q}` that is zero on singletons.
        We return the tuple :math:`(P,\lambda)`, where :math:`P` is a
        :class:`~improb.lowprev.prob.Prob`. In case :math:`\lambda=0` we return
        the tuple (``None``, 0).

        >>> pspace = PSpace('abc')
        >>> lprob = LowProb(pspace, number_type='fraction')
        >>> event = lambda A: Event(pspace, A)
        >>> lprob.set_lower(event('a'), '1/8')
        >>> lprob.set_lower(event('b'), '1/7')
        >>> lprob.set_lower(event('c'), '1/6')
        >>> lprob.set_lower(event('ac'), '3/8')
        >>> lprob.extend()
        >>> print(lprob)
              : 0
        a     : 1/8
          b   : 1/7
            c : 1/6
        a b   : 15/56
        a   c : 3/8
          b c : 13/42
        a b c : 1
        >>> prob, coeff = lprob.get_precise_part()
        >>> print(prob)
        a : 21/73
        b : 24/73
        c : 28/73
        >>> coeff
        Fraction(73, 168)

        .. warning::

            The lower probability must be defined for all singletons. If
            needed, call :meth:`~improb.lowprev.lowpoly.LowPoly.extend` first.

        """
        pspace = self.pspace
        norm = sum(self.get_lower(event) for event in pspace.subsets(size=1))
        from improb.lowprev.prob import Prob
        if norm == 0:
            return (Prob(pspace=pspace,number_type=self.number_type), 0)
        else:
            return (Prob(pspace=pspace,
                         prob=[self.get_lower(event)/norm
                               for event in pspace.subsets(size=1)],
                         number_type=self.number_type),
                    norm)

    def get_imprecise_part(self):
        """Extract the imprecise part and its relative weight.

        Every coherent lower probability :math:`\underline{P}` can be written
        as a unique convex mixture :math:`\lambda P+(1-\lambda)\underline{Q}`
        of an additive 'precise' part :math:`P` and an 'imprecise' part
        :math:`\underline{Q}` that is zero on singletons.
        We return the tuple :math:`(\underline{Q},1-\lambda)`.

        >>> pspace = PSpace('abc')
        >>> lprob = LowProb(pspace,
        ...                 lprob={'a': '1/8', 'b': '1/7', 'c': '1/6'},
        ...                 number_type='fraction')
        >>> print(lprob)
        a     : 1/8
          b   : 1/7
            c : 1/6
        >>> lprob.extend()
        >>> print(lprob)
              : 0
        a     : 1/8
          b   : 1/7
            c : 1/6
        a b   : 15/56
        a   c : 7/24
          b c : 13/42
        a b c : 1
        >>> lprob.set_lower(Event(pspace, 'ac'), '1/3')
        >>> prob, coeff  = lprob.get_precise_part()
        >>> print(prob)
        a : 21/73
        b : 24/73
        c : 28/73
        >>> print(coeff)
        73/168
        >>> improb, cocoeff  = lprob.get_imprecise_part()
        >>> print(cocoeff)
        95/168
        >>> print(improb)
              : 0
        a     : 0
          b   : 0
            c : 0
        a b   : 0
        a   c : 7/95
          b c : 0
        a b c : 1
        >>> coeff + cocoeff == 1
        True

        .. warning::

            The lower probability must be defined for all singletons. If
            needed, call :meth:`~improb.lowprev.lowpoly.LowPoly.extend` first.
        """
        prob, coeff = self.get_precise_part()
        if coeff == 0:
            return self
        else:
            prob = LowProb(self.pspace, mapping=dict((gamble, (lprev, None))
                                                    for gamble, (lprev, uprev)
                                                    in prob.iteritems()),
                          number_type=prob.number_type)
            prob.extend(self.iterkeys(), upper=False)
            return ((1 / (1 - coeff)) * (self - coeff * prob), 1 - coeff)

    def get_outer_approx(self, algorithm=None):
        """Generate an outer approximation.

        :parameter algorithm: a :class:`~string` denoting the algorithm used:
            ``None``, ``'linvac'``, ``'irm'``, ``'imrm'``, or ``'lpbelfunc'``
        :rtype: :class:`~improb.lowprev.lowprob.LowProb`

        This method replaces the lower probability :math:`\underline{P}` by
        a lower probability :math:`\underline{R}` determined by the
        ``algorithm`` argument:

        ``None``
            returns the original lower probability.

            >>> pspace = PSpace('abc')
            >>> lprob = LowProb(pspace,
            ...             lprob={'ab': .5, 'ac': .5, 'bc': .5},
            ...             number_type='fraction')
            >>> lprob.extend()
            >>> print(lprob)
                  : 0
            a     : 0
              b   : 0
                c : 0
            a b   : 1/2
            a   c : 1/2
              b c : 1/2
            a b c : 1
            >>> lprob == lprob.get_outer_approx()
            True

        ``'linvac'``
            replaces the imprecise part :math:`\underline{Q}` by the vacuous
            lower probability :math:`\underline{R}=\min` to generate a simple
            outer approximation.

        ``'irm'``
            replaces :math:`\underline{P}` by a completely monotone lower
            probability :math:`\underline{R}` that is obtained by using the
            IRM algorithm of Hall & Lawry [#hall2004]_. The Moebius transform
            of a lower probability that is not completely monotone contains
            negative belief assignments. Consider such a lower probability and
            an event with such a negative belief assignment. The approximation
            consists of removing this negative assignment and compensating for
            this by correspondingly reducing the positive masses for events
            below it; for details, see the paper.

            The following example illustrates the procedure:

            >>> pspace = PSpace('abc')
            >>> lprob = LowProb(pspace,
            ...             lprob={'ab': .5, 'ac': .5, 'bc': .5},
            ...             number_type='fraction')
            >>> lprob.extend()
            >>> print(lprob)
                  : 0
            a     : 0
              b   : 0
                c : 0
            a b   : 1/2
            a   c : 1/2
              b c : 1/2
            a b c : 1
            >>> lprob.is_completely_monotone()
            False
            >>> print(lprob.mobius)
                  : 0
            a     : 0
              b   : 0
                c : 0
            a b   : 1/2
            a   c : 1/2
              b c : 1/2
            a b c : -1/2
            >>> belfunc = lprob.get_outer_approx('irm')
            >>> print(belfunc.mobius)
                  : 0
            a     : 0
              b   : 0
                c : 0
            a b   : 1/3
            a   c : 1/3
              b c : 1/3
            a b c : 0
            >>> print(belfunc)
                  : 0
            a     : 0
              b   : 0
                c : 0
            a b   : 1/3
            a   c : 1/3
              b c : 1/3
            a b c : 1
            >>> belfunc.is_completely_monotone()
            True

            The next is Example 2 from Hall & Lawry's 2004 paper [#hall2004]_:

            >>> pspace = PSpace('ABCD')
            >>> lprob = LowProb(pspace, lprob={'': 0, 'ABCD': 1,
            ...                                'A': .0895, 'B': .2743,
            ...                                'C': .2668, 'D': .1063,
            ...                                'AB': .3947, 'AC': .4506,
            ...                                'AD': .2959, 'BC': .5837,
            ...                                'BD': .4835, 'CD': .4079,
            ...                                'ABC': .7248, 'ABD': .6224,
            ...                                'ACD': .6072, 'BCD': .7502})
            >>> lprob.is_avoiding_sure_loss()
            True
            >>> lprob.is_coherent()
            False
            >>> lprob.is_completely_monotone()
            False
            >>> belfunc = lprob.get_outer_approx('irm')
            >>> belfunc.is_completely_monotone()
            True
            >>> print(lprob)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.3947
            A   C   : 0.4506
            A     D : 0.2959
              B C   : 0.5837
              B   D : 0.4835
                C D : 0.4079
            A B C   : 0.7248
            A B   D : 0.6224
            A   C D : 0.6072
              B C D : 0.7502
            A B C D : 1.0
            >>> print(belfunc)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.375789766751
            A   C   : 0.405080300695
            A     D : 0.259553087227
              B C   : 0.560442004097
              B   D : 0.43812301076
                C D : 0.399034985143
            A B C   : 0.710712071543
            A B   D : 0.603365864737
            A   C D : 0.601068373065
              B C D : 0.7502
            A B C D : 1.0
            >>> print(lprob.mobius)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.0309
            A   C   : 0.0943
            A     D : 0.1001
              B C   : 0.0426
              B   D : 0.1029
                C D : 0.0348
            A B C   : -0.0736
            A B   D : -0.0816
            A   C D : -0.0846
              B C D : -0.0775
            A B C D : 0.1748
            >>> print(belfunc.mobius)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.0119897667507
            A   C   : 0.0487803006948
            A     D : 0.0637530872268
              B C   : 0.019342004097
              B   D : 0.0575230107598
                C D : 0.0259349851432
            A B C   : 3.33066907388e-16
            A B   D : -1.11022302463e-16
            A   C D : -1.11022302463e-16
              B C D : 0.0
            A B C D : 0.0357768453276
            >>> sum(lprev for (lprev, uprev)
            ...           in (lprob - belfunc).itervalues())/(2 ** len(pspace))
            0.013595658498933991

            .. note::

                This algorithm is *not* invariant under permutation of the
                possibility space.

            .. warning::

                The lower probability must be defined for all events. If
                needed, call :meth:`~improb.lowprev.lowpoly.LowPoly.extend`
                first.

        ``'imrm'``
            replaces :math:`\underline{P}` by a completely monotone lower
            probability :math:`\underline{R}` that is obtained by using an
            algorithm by Quaeghebeur that is as of yet unpublished.

            We apply it to Example 2 from Hall & Lawry's 2004 paper
            [#hall2004]_:

            >>> pspace = PSpace('ABCD')
            >>> lprob = LowProb(pspace, lprob={
            ...     '': 0, 'ABCD': 1,
            ...     'A': .0895, 'B': .2743,
            ...     'C': .2668, 'D': .1063,
            ...     'AB': .3947, 'AC': .4506,
            ...     'AD': .2959, 'BC': .5837,
            ...     'BD': .4835, 'CD': .4079,
            ...     'ABC': .7248, 'ABD': .6224,
            ...     'ACD': .6072, 'BCD': .7502})
            >>> belfunc = lprob.get_outer_approx('imrm')
            >>> belfunc.is_completely_monotone()
            True
            >>> print(lprob)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.3947
            A   C   : 0.4506
            A     D : 0.2959
              B C   : 0.5837
              B   D : 0.4835
                C D : 0.4079
            A B C   : 0.7248
            A B   D : 0.6224
            A   C D : 0.6072
              B C D : 0.7502
            A B C D : 1.0
            >>> print(belfunc)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.381007057096
            A   C   : 0.411644226231
            A     D : 0.26007767078
              B C   : 0.562748716673
              B   D : 0.4404197271
                C D : 0.394394926787
            A B C   : 0.7248
            A B   D : 0.6224
            A   C D : 0.6072
              B C D : 0.7502
            A B C D : 1.0
            >>> print(lprob.mobius)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.0309
            A   C   : 0.0943
            A     D : 0.1001
              B C   : 0.0426
              B   D : 0.1029
                C D : 0.0348
            A B C   : -0.0736
            A B   D : -0.0816
            A   C D : -0.0846
              B C D : -0.0775
            A B C D : 0.1748
            >>> print(belfunc.mobius)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.0172070570962
            A   C   : 0.0553442262305
            A     D : 0.0642776707797
              B C   : 0.0216487166733
              B   D : 0.0598197271
                C D : 0.0212949267869
            A B C   : 2.22044604925e-16
            A B   D : 0.0109955450242
            A   C D : 0.00368317620293
              B C D : 3.66294398528e-05
            A B C D : 0.00879232466651
            >>> sum(lprev for (lprev, uprev)
            ...           in (lprob - belfunc).itervalues())/(2 ** len(pspace))
            0.010375479708342836

            .. note::

                This algorithm *is* invariant under permutation of the
                possibility space.

            .. warning::

                The lower probability must be defined for all events. If
                needed, call :meth:`~improb.lowprev.lowpoly.LowPoly.extend`
                first.

        ``'lpbelfunc'``
            replaces :math:`\underline{P}` by a completely monotone lower
            probability :math:`\underline{R}_\mu` that is obtained via the zeta
            transform of the basic belief assignment :math:`\mu`, a solution of
            the following optimization (linear programming) problem:

            .. math::

                \min\{
                \sum_{A\subseteq\Omega}(\underline{P}(A)-\underline{R}_\mu(A)):
                \mu(A)\geq0, \sum_{B\subseteq\Omega}\mu(B)=1,
                \underline{R}_\mu(A)\leq\underline{P}(A), A\subseteq\Omega
                \},

            which, because constants in the objective function do not influence
            the solution and because
            :math:`\underline{R}_\mu(A)=\sum_{B\subseteq A}\mu(B)`,
            is equivalent to:

            .. math::

                \max\{
                \sum_{B\subseteq\Omega}2^{|\Omega|-|B|}\mu(B):
                \mu(A)\geq0, \sum_{B\subseteq\Omega}\mu(B)=1,
                \sum_{B\subseteq A}\mu(B)
                 \leq\underline{P}(A), A\subseteq\Omega
                \},

            the version that is implemented.

            We apply this to Example 2 from Hall & Lawry's 2004 paper
            [#hall2004]_, which we also used for ``'irm'``:

            >>> pspace = PSpace('ABCD')
            >>> lprob = LowProb(pspace, lprob={'': 0, 'ABCD': 1,
            ...                                'A': .0895, 'B': .2743,
            ...                                'C': .2668, 'D': .1063,
            ...                                'AB': .3947, 'AC': .4506,
            ...                                'AD': .2959, 'BC': .5837,
            ...                                'BD': .4835, 'CD': .4079,
            ...                                'ABC': .7248, 'ABD': .6224,
            ...                                'ACD': .6072, 'BCD': .7502})
            >>> belfunc = lprob.get_outer_approx('lpbelfunc')
            >>> belfunc.is_completely_monotone()
            True
            >>> print(lprob)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.3947
            A   C   : 0.4506
            A     D : 0.2959
              B C   : 0.5837
              B   D : 0.4835
                C D : 0.4079
            A B C   : 0.7248
            A B   D : 0.6224
            A   C D : 0.6072
              B C D : 0.7502
            A B C D : 1.0
            >>> print(belfunc)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.3638
            A   C   : 0.4079
            A     D : 0.28835
              B C   : 0.5837
              B   D : 0.44035
                C D : 0.37355
            A B C   : 0.7248
            A B   D : 0.6224
            A   C D : 0.6072
              B C D : 0.7502
            A B C D : 1.0
            >>> print(lprob.mobius)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.0309
            A   C   : 0.0943
            A     D : 0.1001
              B C   : 0.0426
              B   D : 0.1029
                C D : 0.0348
            A B C   : -0.0736
            A B   D : -0.0816
            A   C D : -0.0846
              B C D : -0.0775
            A B C D : 0.1748
            >>> print(belfunc.mobius)
                    : 0.0
            A       : 0.0895
              B     : 0.2743
                C   : 0.2668
                  D : 0.1063
            A B     : 0.0
            A   C   : 0.0516
            A     D : 0.09255
              B C   : 0.0426
              B   D : 0.05975
                C D : 0.00045
            A B C   : 0.0
            A B   D : 1.11022302463e-16
            A   C D : 0.0
              B C D : 0.0
            A B C D : 0.01615
            >>> sum(lprev for (lprev, uprev)
            ...           in (lprob - belfunc).itervalues())/(2 ** len(pspace)
            ...     ) # doctest: +ELLIPSIS
            0.00991562...

            .. note::

                This algorithm is *not* invariant under permutation of the
                possibility space or changes in the LP-solver:
                there may be a nontrivial convex set of optimal solutions.

            .. warning::

                The lower probability must be defined for all events. If
                needed, call :meth:`~improb.lowprev.lowpoly.LowPoly.extend`
                first.

        """
        if algorithm is None:
            return self
        elif algorithm == 'linvac':
            prob, coeff = self.get_precise_part()
            return prob.get_linvac(1 - coeff)
        elif algorithm == 'irm':
            # Initialize the algorithm
            pspace = self.pspace
            bba = SetFunction(pspace, number_type=self.number_type)
            bba[False] = 0
            def mass_below(event):
                subevents = pspace.subsets(event, full=False, empty=False)
                return sum(bba[subevent] for subevent in subevents)
            def basin_for_negmass(event):
                mass = 0
                index = len(event)
                while bba[event] + mass < 0:
                    index -= 1
                    subevents = pspace.subsets(event, size=index)
                    mass += sum(bba[subevent] for subevent in subevents)
                return (index, mass)
            lprob = self.set_function
            # The algoritm itself:
            # we climb the algebra of events, calculating the belief assignment
            # for each and compensate negative ones by proportionally reducing
            # the assignments in the smallest basin of subevents needed
            for cardinality in range(1,len(pspace) + 1):
                for event in pspace.subsets(size=cardinality):
                    bba[event] = lprob[event] - mass_below(event)
                    if bba[event] < 0:
                        index, mass = basin_for_negmass(event)
                        subevents = chain.from_iterable(
                                        pspace.subsets(event, size=k)
                                            for k in range(index, cardinality))
                        for subevent in subevents:
                            bba[subevent] = (bba[subevent]
                                             * (1 + (bba[event] / mass)))
                        bba[event] = 0
            return LowProb(pspace, lprob=dict((event, bba.get_zeta(event)) 
                                              for event in bba.iterkeys()))
        elif algorithm == 'imrm':
            # Initialize the algorithm
            pspace = self.pspace
            number_type = self.number_type
            bba = SetFunction(pspace, number_type=number_type)
            bba[False] = 0
            def mass_below(event, cardinality=None):
                subevents = pspace.subsets(event, full=False, empty=False,
                                           size=cardinality)
                return sum(bba[subevent] for subevent in subevents)
            def basin_for_negmass(event):
                mass = 0
                index = len(event)
                while bba[event] + mass < 0:
                    index -= 1
                    subevents = pspace.subsets(event, size=index)
                    mass += sum(bba[subevent] for subevent in subevents)
                return (index, mass)
            lprob = self.set_function
            # The algorithm itself:
            cardinality = 1
            while cardinality <= len(pspace):
                temp_bba = SetFunction(pspace, number_type=number_type)
                for event in pspace.subsets(size=cardinality):
                    bba[event] = lprob[event] - mass_below(event)
                offenders = dict((event, basin_for_negmass(event))
                                 for event in pspace.subsets(size=cardinality)
                                 if bba[event] < 0)
                if len(offenders) == 0:
                    cardinality += 1
                else:
                    minindex = min(pair[0] for pair in offenders.itervalues())
                    for event in offenders:
                        if offenders[event][0] == minindex:
                            mass = mass_below(event, cardinality=minindex)
                            scalef = (offenders[event][1] + bba[event]) / mass
                            for subevent in pspace.subsets(event,
                                                           size=minindex):
                                if subevent not in temp_bba:
                                    temp_bba[subevent] = 0
                                temp_bba[subevent] = max(temp_bba[subevent],
                                                         scalef * bba[subevent])
                    for event, value in temp_bba.iteritems():
                        bba[event] = value
                    cardinality = minindex + 1
            return LowProb(pspace, lprob=dict((event, bba.get_zeta(event))
                                              for event in bba.iterkeys()))
        elif algorithm == 'lpbelfunc':
            # Initialize the algorithm
            lprob = self.set_function
            pspace = lprob.pspace
            number_type = lprob.number_type
            n = 2 ** len(pspace)
            # Set up the linear program
            mat = cdd.Matrix(list(chain(
                      [[-1] + n * [1], [1] + n * [-1]],
                      [[0] + [int(event == other)
                              for other in pspace.subsets()]
                       for event in pspace.subsets()],
                      [[lprob[event]] + [-int(other <= event)
                                         for other in pspace.subsets()]
                       for event in pspace.subsets()]
                  )), number_type=number_type)
            mat.obj_type = cdd.LPObjType.MAX
            mat.obj_func = (0,) + tuple(2 ** (len(pspace) - len(event))
                                        for event in pspace.subsets())
            lp = cdd.LinProg(mat)
            # Solve the linear program and check the solution
            lp.solve()
            if lp.status == cdd.LPStatusType.OPTIMAL:
                bba = SetFunction(pspace,
                                  data=dict(izip(list(pspace.subsets()),
                                                 list(lp.primal_solution))),
                                  number_type=number_type)
                return LowProb(pspace, lprob=dict((event, bba.get_zeta(event))
                                                  for event in bba.iterkeys()))
            else:
                raise RuntimeError('No optimal solution found.')
        else:
            raise NotImplementedError
