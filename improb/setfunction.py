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

import collections

from improb import PSpace, Gamble, Event, _fraction, _fraction_repr

class SetFunction(collections.MutableMapping):
    """A real-valued set function defined on the power set of a
    possibility space.

    Bases: :class:`collections.MutableMapping`
    """

    def __init__(self, pspace, mapping=None):
        """Construct a set function on the power set of the given
        possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param mapping: A mapping that defines the value on each event (missing values default to zero).
        :type mapping: :class:`dict`
        """
        self._pspace = PSpace.make(pspace)
        if mapping is not None:
            self._data = dict((Event(pspace, subset), _fraction(value))
                              for subset, value in mapping.iteritems()
                              if _fraction(value) != 0)
        else:
            self._data = {}

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        # iter(self._data) has no stable ordering
        # therefore use self.pspace.subsets() instead
        for subset in self.pspace.subsets():
            if subset in self._data:
                yield subset

    def __contains__(self, event):
        return Event.make(self.pspace, event) in self._data

    def __getitem__(self, event):
        event = Event.make(self.pspace, event)
        try:
            return self._data[event]
        except KeyError:
            return _fraction(0)

    def __setitem__(self, event, value):
        event = Event.make(self.pspace, event)
        value = _fraction(value)
        if value != 0:
            self._data[event] = _fraction(value)
        else:
            del self._data[event]

    def __delitem__(self, event):
        del self._data[Event.make(self.pspace, event)]

    def __repr__(self):
        """
        >>> SetFunction(3, {(): 1, (0, 2): Fraction(21, 10), (0, 1, 2): Fraction(1, 3)}) # doctest: +NORMALIZE_WHITESPACE
        SetFunction(pspace=PSpace(3),
                    mapping={(): 1, (0, 2): '2.1', (0, 1, 2): '1/3'})
        """
        dict_ = [(tuple(omega for omega in self.pspace
                        if omega in event),
                  _fraction_repr(value))
                 for event, value in self.iteritems()]
        return "SetFunction(pspace={0}, mapping={{{1}}})".format(
            repr(self._pspace), ", ".join("{0}: {1}".format(*element)
                                          for element in dict_))

    def __str__(self):
        """
        >>> print(SetFunction('abc', {'': 1, 'ac': 2, 'abc': 5}))
              : 1.000
        a   c : 2.000
        a b c : 5.000
        """
        maxlen_pspace = max(len(str(omega)) for omega in self._pspace)
        maxlen_value = max(len("{0:.3f}".format(float(value)))
                           for value in self.itervalues())
        return "\n".join(
            " ".join("{0: <{1}}".format(omega if omega in event else '',
                                        maxlen_pspace)
                      for omega in self._pspace) +
            " : " +
            "{0:{1}.3f}".format(float(value), maxlen_value)
            for event, value in self.iteritems())

    @property
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace

    def get_mobius_inverse(self):
        """Calculate the mobius inverse.

        >>> setfunc = SetFunction(PSpace('ab'), {'a': 0.25, 'b': 0.25, 'ab': 1})
        >>> print(setfunc.get_mobius_inverse())
        a   : 0.250
          b : 0.250
        a b : 0.500
        """
        return SetFunction(
            self.pspace,
            dict((event,
                  sum(((-1) ** len(event - subevent)) * self[subevent]
                      for subevent in self.pspace.subsets(event)))
                 for event in self.pspace.subsets()))

