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

from improb import PSpace, Gamble, Event

class SetFunction(collections.MutableMapping, cdd.NumberTypeable):
    """A real-valued set function defined on the power set of a
    possibility space.

    Bases: :class:`collections.MutableMapping`, :class:`cdd.NumberTypeable`
    """

    _constraints_bba_n_monotone = {}
    """Caches the constraints calculated for n-monotonicity."""

    def __init__(self, pspace, data=None, number_type='float'):
        """Construct a set function on the power set of the given
        possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param data: A mapping that defines the value on each event (missing values default to zero).
        :type data: :class:`dict`
        """
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
        >>> SetFunction(pspace=3, data={(): '1.0', (0, 2): '2.1', (0, 1, 2): '1/3'}, number_type='float') # doctest: +NORMALIZE_WHITESPACE
        SetFunction(pspace=PSpace(3),
                    data={(): 1.0,
                          (0, 2): 2.1000000000000001,
                          (0, 1, 2): 0.33333333333333331},
                    number_type='float')
        >>> SetFunction(pspace=3, data={(): '1.0', (0, 2): '2.1', (0, 1, 2): '1/3'}, number_type='fraction') # doctest: +NORMALIZE_WHITESPACE
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
        >>> print(SetFunction(pspace='abc', data={'': 1, 'ac': 2, 'abc': '3.1'}, number_type='fraction'))
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

    def get_mobius(self, event):
        """Calculate the value of the Mobius transform of the given
        event. The Mobius transform of a set function :math:`s` is
        given by the formula:

        .. math::

           m(A)=
           \sum_{B\subseteq A}(-1)^{|A\setminus B|}s(B)

        for any event :math:`A` (note that it is usually assumed that
        :math:`s(\emptyset)=0`).

        .. warning::

           The set function must be defined for all subsets of the
           given event.

        >>> setfunc = SetFunction(pspace='ab', data={'': 0, 'a': 0.25, 'b': 0.3, 'ab': 1}, number_type='float')
        >>> print(setfunc)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 1.0
        >>> inv = SetFunction(pspace='ab',
        ...                   data=dict((event, setfunc.get_mobius(event))
        ...                        for event in setfunc.pspace.subsets()),
        ...                   number_type='float')
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
        ...     data={'': 0, 'a': 0.25, 'b': 0.3, 'ab': 0.45},
        ...     number_type='float')
        >>> print(setfunc)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 0.45
        >>> inv = SetFunction(pspace='ab',
        ...                   data=dict((event, setfunc.get_zeta(event))
        ...                             for event in setfunc.pspace.subsets()),
        ...                   number_type='float')
        >>> print(inv)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 1.0
        """
        event = self.pspace.make_event(event)
        return sum(self[subevent] for subevent in self.pspace.subsets(event))

    @classmethod
    def get_constraints_bba_n_monotone(cls, pspace, monotonicity=None):
        """Yields constraints for basic belief assignments with given
        monotonicity. This follows the algorithm described in
        Proposition 4 of *Chateauneuf and Jaffray. Some
        characterizations of lower probabilities and other monotone
        capacities through the use of Mobius inversion. Mathematical
        Social Sciences 17(3), pages 263-283*.

        The elements are the coefficients on the basic belief
        assignments of events, following the ordering of
        ``pspace.subsets()``. The constant term is always zero so is
        omitted.

        .. note::

            The trivial constraints that the empty set must have mass
            zero, and that the masses must sum to one, are not
            included.

        .. note::

            To get *all* the constraints for n-monotonicity, call this
            method with monotonicity=xrange(1, n + 1).

        .. note::

            The result is cached, for speed.

        >>> pspace = "abc"
        >>> for mono in xrange(1, len(pspace) + 1):
        ...     print("{0} monotonicity:".format(mono))
        ...     print(" ".join("{0:<{1}}".format("".join(i for i in event), len(pspace))
        ...                    for event in PSpace(pspace).subsets()))
        ...     for constraint in sorted(
        ...         SetFunction.get_constraints_bba_n_monotone(pspace, mono)):
        ...         print(" ".join("{0:<{1}}".format(value, len(pspace))
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
        if monotonicity <= 0:
            raise ValueError("specify a strictly positive monotonicity")
        # try cached version
        try:
            constraints = cls._constraints_bba_n_monotone[len(pspace), monotonicity]
        except KeyError:
            pass
        else:
            for constraint in constraints:
                yield constraint
            return
        # not in cache: calculate it
        constraints = []
        for event in pspace.subsets(size=xrange(monotonicity, len(pspace) + 1)):
            for subevent in pspace.subsets(event, size=monotonicity):
                midevents = set(pspace.subsets(event, contains=subevent))
                constraint = [1 if midevent in midevents else 0
                              for midevent in pspace.subsets()]
                yield constraint
                constraints.append(constraint)
        # save result in cache
        cls._constraints_bba_n_monotone[len(pspace), monotonicity] = constraints
