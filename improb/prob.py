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

"""A module for working with probability measures."""

import collections

from improb import PSpace, Gamble, Event

class Prob(collections.Mapping, collections.Hashable):
    """A probability measure.

    >>> from improb.prob import Prob
    >>> p = Prob(5, [0.1, 0.2, 0.3, 0.05, 0.35])
    >>> print(p)
    0 : 0.100
    1 : 0.200
    2 : 0.300
    3 : 0.050
    4 : 0.350
    >>> print("{0:.6f}".format(p.get_prev([2, 4, 3, 8, 1])))
    2.650000
    >>> print("{0:.6f}".format(p.get_prev([2, 4, 3, 8, 1], [0, 1])))
    3.333333
    """

    def __init__(self, pspace, mapping):
        """Construct a probability measure on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param mapping: A mapping that defines the probability of each atom.
        :type mapping: :class:`dict`
        """

        self._pspace = PSpace.make(pspace)
        self._prob = dict((omega, float(mapping[omega]))
                          for omega in self.pspace)

    def __len__(self):
        return len(self._prob)

    def __iter__(self):
        return iter(self._prob)

    def __contains__(self, event):
        return omega in self._prob

    def __getitem__(self, omega):
        return self._prob[omega]

    def __str__(self):
        return str(Gamble(self.pspace, self))

    def get_prev(self, gamble, event=None, tolerance=1e-6):
        gamble = Gamble.make(self.pspace, gamble)
        if event is None:
            return sum(self[omega] * gamble[omega] for omega in self.pspace)
        else:
            event = Event.make(self.pspace, event)
            event_prob = self.get_prev(event.indicator())
            if event_prob < tolerance:
                raise ZeroDivisionError(
                    "cannot condition on event with zero probability")
            return self.get_prev(gamble * event) / event_prob

    @property
    def pspace(self):
        """An :class:`improb.PSpace` representing the possibility space."""
        return self._pspace
