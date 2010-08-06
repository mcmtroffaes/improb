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

from cdd import NumberTypeable
import collections

from improb import PSpace, Gamble, Event

class SetFunction(collections.MutableMapping, NumberTypeable):
    """A real-valued set function defined on the power set of a
    possibility space.

    Bases: :class:`collections.MutableMapping`, :class:`~improb.NumberTypeable`
    """

    def __init__(self, pspace, data=None, number_type='float'):
        """Construct a set function on the power set of the given
        possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param data: A mapping that defines the value on each event (missing values default to zero).
        :type data: :class:`dict`
        """
        NumberTypeable.__init__(self, number_type)
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
        >>> SetFunction(3, {(): '1.0', (0, 2): '2.1', (0, 1, 2): '1/3'}, 'float') # doctest: +NORMALIZE_WHITESPACE
        SetFunction(pspace=PSpace(3),
                    data={(): 1.0,
                          (0, 2): 2.1000000000000001,
                          (0, 1, 2): 0.33333333333333331},
                    number_type='float')
        >>> SetFunction(3, {(): '1.0', (0, 2): '2.1', (0, 1, 2): '1/3'}, 'fraction') # doctest: +NORMALIZE_WHITESPACE
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
        >>> print(SetFunction('abc', {'': 1, 'ac': 2, 'abc': '3.1'}, 'fraction'))
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

        >>> setfunc = SetFunction(PSpace('ab'), {'': 0, 'a': 0.25, 'b': 0.3, 'ab': 1}, 'float')
        >>> print(setfunc)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 1.0
        >>> inv = SetFunction(setfunc.pspace,
        ...                   dict((event, setfunc.get_mobius(event))
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

    def get_mobius_inverse(self, event):
        """Calculate the value of the inverse Mobius transform of the
        given event. The inverse Mobius transform of a set function :math:`m`
        is given by the formula:

        .. math::

           s(A)=
           \sum_{B\subseteq A}m(B)

        for any event :math:`A` (note that it is usually assumed that
        :math:`m(\emptyset)=0`).

        .. warning::

           The set function must be defined for all subsets of the
           given event.

        >>> setfunc = SetFunction(PSpace('ab'), {'': 0, 'a': 0.25, 'b': 0.3, 'ab': 0.45}, 'float')
        >>> print(setfunc)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 0.45
        >>> inv = SetFunction(setfunc.pspace,
        ...                   dict((event, setfunc.get_mobius_inverse(event))
        ...                        for event in setfunc.pspace.subsets()))
        >>> print(inv)
            : 0.0
        a   : 0.25
          b : 0.3
        a b : 1.0
        """
        event = self.pspace.make_event(event)
        return sum(self[subevent] for subevent in self.pspace.subsets(event))
