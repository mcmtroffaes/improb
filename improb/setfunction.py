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

"""Set functions."""

from __future__ import division, absolute_import, print_function

import cdd
import collections
import itertools
import operator

from improb import PSpace, Gamble, Event

class SetFunction(collections.MutableMapping, cdd.NumberTypeable):
    """A real-valued set function defined on the power set of a
    possibility space.

    Bases: :class:`collections.MutableMapping`, :class:`cdd.NumberTypeable`
    """

    def __init__(self, pspace, data=None, number_type=None):
        """Construct a set function on the power set of the given
        possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param data: A mapping that defines the value on each event (missing values default to zero).
        :type data: :class:`dict`
        """
        if number_type is None:
            if data is not None:
                number_type = cdd.get_number_type_from_sequences(
                    data.itervalues())
            else:
                number_type = 'float'
        cdd.NumberTypeable.__init__(self, number_type)
        self._pspace = PSpace.make(pspace)
        self._data = {}
        if data is not None:
            for event, value in data.iteritems():
                self[event] = value

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        # iter(self._data) has no stable ordering
        # therefore use self.pspace.subsets() instead
        for subset in self.pspace.subsets():
            if subset in self._data:
                yield subset

    def __contains__(self, event):
        return self.pspace.make_event(event) in self._data

    def __getitem__(self, event):
        event = self.pspace.make_event(event)
        return self._data[event]

    def __setitem__(self, event, value):
        event = self.pspace.make_event(event)
        value = self.make_number(value)
        self._data[event] = value

    def __delitem__(self, event):
        del self._data[self.pspace.make_event(event)]

    def __repr__(self):
        """
        >>> SetFunction(pspace=3, data={(): 1, (0, 2): 2.1, (0, 1, 2): '1/3'}) # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        SetFunction(pspace=PSpace(3),
                    data={(): 1.0,
                          (0, 2): 2.1,
                          (0, 1, 2): 0.333...},
                    number_type='float')
        >>> SetFunction(pspace=3, data={(): '1.0', (0, 2): '2.1', (0, 1, 2): '1/3'}) # doctest: +NORMALIZE_WHITESPACE
        SetFunction(pspace=PSpace(3),
                    data={(): 1,
                          (0, 2): '21/10',
                          (0, 1, 2): '1/3'},
                    number_type='fraction')
        """
        dict_ = [(tuple(omega for omega in self.pspace
                        if omega in event),
                  self.number_repr(value))
                 for event, value in self.iteritems()]
        return "SetFunction(pspace={0}, data={{{1}}}, number_type={2})".format(
            repr(self.pspace),
            ", ".join("{0}: {1}".format(*element) for element in dict_),
            repr(self.number_type))

    def __str__(self):
        """
        >>> print(SetFunction(pspace='abc', data={'': '1', 'ac': '2', 'abc': '3.1'}))
              : 1
        a   c : 2
        a b c : 31/10
        """
        maxlen_pspace = max(len(str(omega)) for omega in self._pspace)
        return "\n".join(
            " ".join("{0: <{1}}".format(omega if omega in event else '',
                                        maxlen_pspace)
                      for omega in self._pspace) +
            " : {0}".format(self.number_str(value))
            for event, value in self.iteritems())

    @property
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace

    def make_gamble(self, gamble):
        return self.pspace.make_gamble(gamble, self.number_type)

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

        >>> setfunc = SetFunction(pspace='ab', data={'': 0, 'a': 0.25, 'b': 0.3, 'ab': 1})
        >>> print(setfunc)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 1.0
        >>> inv = SetFunction(pspace='ab',
        ...                   data=dict((event, setfunc.get_mobius(event))
        ...                        for event in setfunc.pspace.subsets()))
        >>> print(inv)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 0.45
        """
        event = self.pspace.make_event(event)
        return sum(((-1) ** len(event - subevent)) * self[subevent]
                   for subevent in self.pspace.subsets(event))

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

        >>> setfunc = SetFunction(
        ...     pspace='ab',
        ...     data={'': 0, 'a': 0.25, 'b': 0.3, 'ab': 0.45})
        >>> print(setfunc)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 0.45
        >>> inv = SetFunction(pspace='ab',
        ...                   data=dict((event, setfunc.get_zeta(event))
        ...                             for event in setfunc.pspace.subsets()))
        >>> print(inv)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 1.0
        """
        event = self.pspace.make_event(event)
        return sum(self[subevent] for subevent in self.pspace.subsets(event))

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

        >>> s = SetFunction(pspace='abc', data={'': 0,
        ...                                     'a': 0, 'b': 0, 'c': 0,
        ...                                     'ab': .5, 'bc': .5, 'ca': .5,
        ...                                     'abc': 1})
        >>> s.get_choquet([1, 2, 3])
        1.5
        >>> s.get_choquet([1, 2, 2])
        1.5
        >>> s.get_choquet([1, 2, 1])
        1.0

        .. warning::

           The set function must be defined for all level sets :math:`A_i`
           induced by the argument gamble.

           >>> s = SetFunction(pspace='abc', data={'ab': .5, 'bc': .5, 'ca': .5,
           ...                                     'abc': 1})
           >>> s.get_choquet([1, 2, 2])
           1.5
           >>> s.get_choquet([2, 2, 1])
           1.5
           >>> s.get_choquet([-1, -1, -2])
           -1.5
           >>> s.get_choquet([1, 2, 3])
           Traceback (most recent call last):
               ...
           KeyError: Event(pspace=PSpace(['a', 'b', 'c']), elements=set(['c']))
        """
        result = 0
        gamble = self.make_gamble(gamble)
        # find values and level sets of the gamble
        gamble_inverse = collections.defaultdict(set)
        for key, value in gamble.iteritems():
            gamble_inverse[value].add(key)
        items = sorted(gamble_inverse.iteritems())
        # now calculate the Choquet integral
        event = set(self.pspace)
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
        gamble = self.make_gamble(gamble)
        return sum(self[event_] * min(gamble[omega] for omega in event_)
                   for event_ in self.pspace.subsets(empty=False))

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
                sum(self[event] for event in self.pspace.subsets()), 1) != 0:
                return False
        # iterate over all constraints
        for constraint in self.get_constraints_bba_n_monotone(
            self.pspace, monotonicity):
            # check the constraint
            if self.number_cmp(
                sum(self[event] for event in constraint)) < 0:
                return False
        return True

    @classmethod
    def get_constraints_bba_n_monotone(cls, pspace, monotonicity=None):
        """Yields constraints for basic belief assignments with given
        monotonicity.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
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

        >>> pspace = "abc"
        >>> for mono in xrange(1, len(pspace) + 1):
        ...     print("{0} monotonicity:".format(mono))
        ...     print(" ".join("{0:<{1}}".format("".join(i for i in event), len(pspace))
        ...                    for event in PSpace(pspace).subsets()))
        ...     constraints = SetFunction.get_constraints_bba_n_monotone(pspace, mono)
        ...     constraints = [set(constraint) for constraint in constraints]
        ...     constraints = [[1 if event in constraint else 0
        ...                     for event in PSpace(pspace).subsets()]
        ...                    for constraint in constraints]
        ...     for constraint in sorted(constraints):
        ...         print(" ".join("{0:<{1}}"
        ...                        .format(value, len(pspace))
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
        pspace = PSpace.make(pspace)
        # check type
        if monotonicity is None:
            raise ValueError("specify monotonicity")
        elif isinstance(monotonicity, collections.Iterable):
            # special case: return it for all values in the iterable
            for mono in monotonicity:
                for constraint in cls.get_constraints_bba_n_monotone(pspace, mono):
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
        for event in pspace.subsets(size=xrange(monotonicity, len(pspace) + 1)):
            for subevent in pspace.subsets(event, size=monotonicity):
                yield pspace.subsets(event, contains=subevent)

    @classmethod
    def make_extreme_bba_n_monotone(cls, pspace, monotonicity=None):
        """Yield extreme basic belief assignments with given monotonicity.

        .. warning::

           Currently this doesn't work very well except for the cases
           below.

        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone('abc', monotonicity=2))
        >>> len(bbas)
        8
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        False
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone('abc', monotonicity=3))
        >>> len(bbas)
        7
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        True
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone('abcd', monotonicity=2))
        >>> len(bbas)
        41
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        False
        >>> all(bba.is_bba_n_monotone(4) for bba in bbas)
        False
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone('abcd', monotonicity=3))
        >>> len(bbas)
        16
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(4) for bba in bbas)
        False
        >>> bbas = list(SetFunction.make_extreme_bba_n_monotone('abcd', monotonicity=4))
        >>> len(bbas)
        15
        >>> all(bba.is_bba_n_monotone(2) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(3) for bba in bbas)
        True
        >>> all(bba.is_bba_n_monotone(4) for bba in bbas)
        True
        >>> # cddlib hangs on larger possibility spaces
        >>> #bbas = list(SetFunction.make_extreme_bba_n_monotone('abcde', monotonicity=2))
        """
        pspace = PSpace.make(pspace)
        # constraint for empty set and full set
        matrix = cdd.Matrix(
            [[0] + [1 if event.is_false() else 0 for event in pspace.subsets()],
             [-1] + [1 for event in pspace.subsets()]],
            linear=True,
            number_type='fraction')
        # constraints for monotonicity
        constraints = [set(constraint) for constraint in
                       cls.get_constraints_bba_n_monotone(
                           pspace, xrange(1, monotonicity + 1))]
        matrix.extend([[0] + [1 if event in constraint else 0
                              for event in pspace.subsets()]
                       for constraint in constraints])
        matrix.rep_type = cdd.RepType.INEQUALITY

        # debug: simplify matrix
        #print(pspace, monotonicity) # debug
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
                pspace=pspace,
                data=dict((event, vert[1 + index])
                           for index, event in enumerate(pspace.subsets())),
                number_type='fraction')

if __name__ == "__main__":
    import doctest
    doctest.testmod()
