# -*- coding: utf-8 -*-
# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2011, Matthias Troffaes
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

"""Set functions."""

from __future__ import division, absolute_import, print_function

import cdd
import collections
import itertools
import operator

from improb._compat import OrderedDict
from improb import Domain, MutableDomain, Func, Set, ABCVar, Var

class SetFunction(collections.MutableMapping):
    """A real-valued set function defined on the power set of a
    possibility space.

    Bases: :class:`collections.MutableMapping`
    """

    def __init__(self, data=None):
        """Construct a set function.

        :param data: A mapping that defines the value on each event.
            Events that are not in the domain map to zero.
        :type data: :class:`~collections.Mapping`
        """
        self._data = {}
        self._domain = MutableDomain()
        if data is not None:
            for event, value in data.iteritems():
                self[event] = value

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, event):
        return Set._make(event) in self._data

    def __getitem__(self, event):
        return self._data[Set._make(event)]

    def __setitem__(self, event, value):
        event = Set._make(event)
        self._data[event] = value
        self._domain |= event.domain

    def __delitem__(self, event):
        del self._data[Set._make(event)]
        # should we update self._domain? slow...

    def __repr__(self):
        """
        >>> from improb import Var
        >>> a = Var([0, 1, 2], name='A')
        >>> SetFunction(data={Set([]): 1, Set([{a: 0}, {a: 2}]): 2.1, Set([{}]): 1/3})
        SetFunction(data={Set([]): 1, Set([{}]): 0.3333333333333333, Set([{Var([0, 1, 2], name='A'): 2}, {Var([0, 1, 2], name='A'): 0}]): 2.1})
        """
        return "SetFunction(data=%s)" % repr(self._data)

    def __str__(self):
        """
        >>> from improb import Var
        >>> a = Var([0, 1, 2], name='A')
        >>> print(SetFunction(data={Set([]): 1, Set([{a: 0}, {a: 2}]): 2.1, Set([{}]): 1/3}))
        {∅: 1,
         Ω: 0.333333333333,
         A=2 | A=0: 2.1}
        """
        items = [(str(event), str(value)) for event, value in self.iteritems()]
        if not items:
            return "{}"
        return "{" + ",\n ".join(
            "{0}: {1}".format(event, value)
            for event, value in items) + "}"

    @property
    def domain(self):
        """A :class:`~improb.MutableDomain` representing the domain."""
        return self._domain

    def get_mobius(self, event):
        """Calculate the value of the Mobius transform of the given
        event. The Mobius transform of a set function :math:`s` is
        given by the formula:

        .. math::

           m(A)=
           \sum_{B\subseteq A}(-1)^{|A\setminus B|}s(B)

        for any event :math:`A`.

        .. warning::

           The set function must be defined for all subsets of the
           given event.

        >>> a = Var('ab', 'A')
        >>> setfunc = SetFunction(data={
        ...     Set([]): 0,
        ...     Set([{a: 'a'}]): 0.25,
        ...     Set([{a: 'b'}]): 0.3,
        ...     Set([{}]): 1,
        ...     })
        >>> print(setfunc)
        {Ω: 1,
         ∅: 0,
         A=b: 0.3,
         A=a: 0.25}
        >>> inv = SetFunction(data=dict(
        ...     (event, setfunc.get_mobius(event))
        ...     for event in setfunc.domain.subsets()))
        >>> print(inv)
        {Ω: 0.45,
         ∅: 0,
         A=b: 0.3,
         A=a: 0.25}
        """
        return sum(((-1) ** len(list((event - subevent).points(self.domain)))) * self[subevent]
                   for subevent in self.domain.subsets(event))

    def get_zeta(self, event):
        """Calculate the value of the zeta transform (inverse Mobius
        transform) of the given event. The zeta transform of a set
        function :math:`m` is given by the formula:

        .. math::

           s(A)=
           \sum_{B\subseteq A}m(B)

        for any event :math:`A` (note that it is usually assumed that
        :math:`m(\emptyset)=0`).

        .. warning::

           The set function must be defined for all subsets of the
           given event.

        >>> a = Var('ab', 'A')
        >>> setfunc = SetFunction(data={
        ...     Set([]): 0,
        ...     Set([{a: 'a'}]): 0.25,
        ...     Set([{a: 'b'}]): 0.3,
        ...     Set([{}]): 0.45,
        ...     })
        >>> inv = SetFunction(data=dict((event, setfunc.get_zeta(event))
        ...                             for event in setfunc.domain.subsets()))
        >>> print(inv)
        {Ω: 1.0,
         ∅: 0,
         A=b: 0.3,
         A=a: 0.25}
        """
        return sum(self[subevent] for subevent in self.domain.subsets(event))

    def get_choquet(self, gamble):
        """Calculate the Choquet integral of the given gamble.

        :parameter gamble: |gambletype|

        The Choquet integral of a set function :math:`s` is given by
        the formula:

        .. math::

          \inf(f)s(\Omega) +
          \int_{\inf(f)}^{\sup(f)}
          s(\{\omega\in\Omega:f(\omega)\geq t\})\mathrm{d}t

        for any gamble :math:`f` (note that it is usually assumed that
        :math:`s(\emptyset)=0`). For the discrete case dealt with here,
        this becomes

        .. math::

           v_0 s(A_0) +
           \sum_{i=1}^{n-1} (v_i-v_{i-1})s(A_i),

        where :math:`v_i` are the
        *unique* values of :math:`f` sorted in increasing order
        and :math:`A_i=\{\omega\in\Omega:f(\omega)\geq v_i\}` are the
        level sets induced.

        >>> from improb import Var
        >>> a = Var('abc')
        >>> s = SetFunction(data={
        ...     Set([]): 0,
        ...     Set([{a: 'a'}]): 0,
        ...     Set([{a: 'b'}]): 0,
        ...     Set([{a: 'c'}]): 0,
        ...     Set([{a: 'a'}, {a: 'b'}]): .5,
        ...     Set([{a: 'a'}, {a: 'c'}]): .5,
        ...     Set([{a: 'b'}, {a: 'c'}]): .5,
        ...     Set([{}]): 1})
        >>> s.get_choquet(Func(a, [1, 2, 3]))
        1.5
        >>> s.get_choquet(Func(a, [1, 2, 2]))
        1.5
        >>> s.get_choquet(Func(a, [1, 2, 1]))
        1

        .. warning::

           The set function must be defined for all level sets :math:`A_i`
           induced by the argument gamble.

           >>> a = Var('abc', name='A')
           >>> s = SetFunction(data={
           ...     Set([{a: 'a'}, {a: 'b'}]): .5,
           ...     Set([{a: 'a'}, {a: 'c'}]): .5,
           ...     Set([{a: 'b'}, {a: 'c'}]): .5,
           ...     Set([{}]): 1})
           >>> s.get_choquet(Func(a, [1, 2, 2]))
           1.5
           >>> s.get_choquet(Func(a, [2, 2, 1]))
           1.5
           >>> s.get_choquet(Func(a, [-1, -1, -2]))
           -1.5
           >>> s.get_choquet(Func(a, [1, 2, 3]))
           Traceback (most recent call last):
               ...
           KeyError: Set([{Var(['a', 'b', 'c'], name='A'): 'c'}])
        """
        result = 0
        if not isinstance(gamble, ABCVar):
            raise TypeError(
                "expected ABCVar but got %s" % gamble.__class__.__name__)
        # find values and level sets of the gamble
        items = sorted(gamble.get_level_sets().iteritems())
        # now calculate the Choquet integral
        event = Set([{}])
        previous_value = 0
        for value, keys in items:
            result += (value - previous_value) * self[event]
            previous_value = value
            event -= keys
        return result

    def get_bba_choquet(self, gamble):
        r"""Calculate the Choquet integral of the set function as a
        basic belief assignment.

        :parameter gamble: |gambletype|

        The Choquet integral of a set function :math:`s` is given by
        the formula:

        .. math::

           \sum_{\emptyset\neq A\subseteq\Omega}
           m(A)\inf_{\omega\in A}f(\omega)

        where :math:`m` is the Mobius transform of :math:`s`.

        .. warning::

            In general,
            :meth:`improb.setfunction.SetFunction.get_choquet` is far
            more efficient.

        .. seealso::

            :meth:`improb.lowprev.lowprob.LowProb.is_completely_monotone`
                To check for complete monotonicity.

            :meth:`improb.setfunction.SetFunction.get_mobius`
                Mobius transform of an arbitrary set function.
        """
        if not isinstance(gamble, ABCVar):
            raise TypeError(
                "expected ABCVar but got %s" % gamble.__class__.__name__)
        return sum(self[event_] * min(gamble.get_value(point) for point in event_)
                   for event_ in self.domain.subsets(empty=False))

    def is_bba_n_monotone(self, monotonicity=None):
        """Is the set function, as basic belief assignment,
        n-monotone, given that it is (n-1)-monotone?

        .. note::

            To check for n-monotonicity, call this method with
            *monotonicity=xrange(n + 1)*.

        .. note::

            For convenience, 0-montonicity is defined as empty set and
            possibility space having lower probability 0 and 1
            respectively.

        .. warning::

           The set function must be defined for all events.
        """
        if monotonicity == 0:
            # check empty set and sum
            if self.number_cmp(self[False]) != 0:
                return False
            if self.number_cmp(
                sum(self[event] for event in self.domain.subsets()), 1) != 0:
                return False
        # iterate over all constraints
        for constraint in self.get_constraints_bba_n_monotone(
            self.domain, monotonicity):
            # check the constraint
            if self.number_cmp(
                sum(self[event] for event in constraint)) < 0:
                return False
        return True

    @classmethod
    def get_constraints_bba_n_monotone(cls, domain, monotonicity=None):
        """Yields constraints for basic belief assignments with given
        monotonicity.

        :param domain: The possibility space.
        :type domain: |domaintype|
        :param monotonicity: Requested level of monotonicity (see
            notes below for details).
        :type monotonicity: :class:`int` or
            :class:`collections.Iterable` of :class:`int`

        This follows the algorithm described in Proposition 2 (for
        1-monotonicity) and Proposition 4 (for n-monotonicity) of
        *Chateauneuf and Jaffray, 1989. Some characterizations of
        lower probabilities and other monotone capacities through the
        use of Mobius inversion. Mathematical Social Sciences 17(3),
        pages 263-283*:

        A set function :math:`s` defined on the power set of
        :math:`\Omega` is :math:`n`-monotone if and only if its Mobius
        transform :math:`m` satisfies:

        .. math::

            m(\emptyset)=0, \qquad\sum_{A\subseteq\Omega} m(A)=1,

        and

        .. math::

            \sum_{B\colon C\subseteq B\subseteq A} m(B)\ge 0

        for all :math:`C\subseteq A\subseteq\Omega`, with
        :math:`1\le|C|\le n`.

        This implementation iterates over all :math:`C\subseteq
        A\subseteq\Omega`, with :math:`|C|=n`, and yields each
        constraint as an iterable of the events :math:`\{B\colon
        C\subseteq B\subseteq A\}`. For example, you can then check
        the constraint by summing over this iterable.

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

            The trivial constraints that the empty set must have mass
            zero, and that the masses must sum to one, are not
            included: so for *monotonicity=0* this method returns an
            empty iterator.

        >>> a = Var('abc', name='A')
        >>> dom = Domain(a)
        >>> for mono in xrange(1, len(a) + 1):
        ...     print("{0} monotonicity:".format(mono))
        ...     print(" ".join("{0:<{1}}".format("".join(sorted(point[a] for point in event.points(dom))), len(a))
        ...                    for event in dom.subsets()))
        ...     constraints = SetFunction.get_constraints_bba_n_monotone(dom, mono)
        ...     constraints = [set(constraint) for constraint in constraints]
        ...     constraints = [[1 if event in constraint else 0
        ...                     for event in dom.subsets()]
        ...                    for constraint in constraints]
        ...     for constraint in sorted(constraints):
        ...         print(" ".join("{0:<{1}}"
        ...                        .format(str(value), len(a))
        ...                        for value in constraint))
        1 monotonicity:
            a   b   c   ab  ac  bc  abc
        0   0   0   1   0   0   0   0  
        0   0   0   1   0   0   1   0  
        0   0   0   1   0   1   0   0  
        0   0   0   1   0   1   1   1  
        0   0   1   0   0   0   0   0  
        0   0   1   0   0   0   1   0  
        0   0   1   0   1   0   0   0  
        0   0   1   0   1   0   1   1  
        0   1   0   0   0   0   0   0  
        0   1   0   0   0   1   0   0  
        0   1   0   0   1   0   0   0  
        0   1   0   0   1   1   0   1  
        2 monotonicity:
            a   b   c   ab  ac  bc  abc
        0   0   0   0   0   0   1   0  
        0   0   0   0   0   0   1   1  
        0   0   0   0   0   1   0   0  
        0   0   0   0   0   1   0   1  
        0   0   0   0   1   0   0   0  
        0   0   0   0   1   0   0   1  
        3 monotonicity:
            a   b   c   ab  ac  bc  abc
        0   0   0   0   0   0   0   1  
        """
        # check type
        if not isinstance(domain, Domain):
            raise TypeError("expected a Domain")
        if monotonicity is None:
            raise ValueError("specify monotonicity")
        elif isinstance(monotonicity, collections.Iterable):
            # special case: return it for all values in the iterable
            for mono in monotonicity:
                for constraint in cls.get_constraints_bba_n_monotone(domain, mono):
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
        for event in domain.subsets(size=xrange(monotonicity, domain.size() + 1)):
            for subevent in domain.subsets(event, size=monotonicity):
                yield domain.subsets(event, contains=subevent)

    @classmethod
    def make_extreme_bba_n_monotone(cls, domain, monotonicity=None):
        """Yield extreme basic belief assignments with given monotonicity.

        .. warning::

           Currently this doesn't work very well except for the cases
           below.

        >>> a = Var('abc')
        >>> dom = Domain(a)
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=2))
        >>> len(bbas)
        8
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        False
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=3))
        >>> len(bbas)
        7
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        True
        >>> a = Var('abcd')
        >>> dom = Domain(a)
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=2))
        >>> len(bbas)
        41
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        False
        >>> all(bba.is_bba_n_monotone(4) for bba in bbas)
        False
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=3))
        >>> len(bbas)
        16
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(4) for bba in bbas)
        False
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=4))
        >>> len(bbas)
        15
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(4) for bba in bbas)
        True
        >>> # cddlib hangs on larger possibility spaces
        >>> #a = Var('abcde')
        >>> #dom = Domain(a)
        >>> #bbas = list(SetFunction.make_extreme_bba_n_monotone(dom, monotonicity=2))
        """
        if not isinstance(domain, Domain):
            raise TypeError("expected Domain")
        # constraint for empty set and full set
        matrix = cdd.Matrix(
            [[0] + [1 if event.is_false() else 0 for event in domain.subsets()],
             [-1] + [1 for event in domain.subsets()]],
            linear=True,
            number_type='fraction')
        # constraints for monotonicity
        constraints = [set(constraint) for constraint in
                       cls.get_constraints_bba_n_monotone(
                           domain, xrange(1, monotonicity + 1))]
        matrix.extend([[0] + [1 if event in constraint else 0
                              for event in domain.subsets()]
                       for constraint in constraints])
        matrix.rep_type = cdd.RepType.INEQUALITY

        # debug: simplify matrix
        #print(domain, monotonicity) # debug
        ##print("original:", len(matrix))
        #matrix.canonicalize()
        #print("new     :", len(matrix))
        #print(matrix) # debug

        # calculate extreme points
        poly = cdd.Polyhedron(matrix)
        # convert these points back to lower probabilities
        #print(poly.get_generators()) # debug
        for vert in poly.get_generators():
            yield cls(
                domain=domain,
                data=dict((event, vert[1 + index])
                           for index, event in enumerate(domain.subsets())),
                number_type='fraction')

if __name__ == "__main__":
    import doctest
    doctest.testmod()
