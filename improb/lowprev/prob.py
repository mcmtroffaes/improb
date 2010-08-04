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

from improb import PSpace, Gamble, Event
from improb.lowprev.linvac import LinVac
from improb.lowprev.lowpoly import LowPoly

class Prob(LinVac):
    """A probability measure.

    >>> p = Prob(5, prob=['0.1', '0.2', '0.3', '0.05', '0.35'])
    >>> print(p)
    0 : 0.100
    1 : 0.200
    2 : 0.300
    3 : 0.050
    4 : 0.350
    >>> print(p.get_prev([2, 4, 3, 8, 1]))
    53/20
    >>> print(p.get_prev([2, 4, 3, 8, 1], [0, 1]))
    10/3
    """

    def __str__(self):
        return str(
            Gamble.make(self.pspace,
                        dict((omega, self[omega, None][0])
                             for omega in self.pspace)))

    def _make_value(self, value):
        lprev, uprev = LowPoly._make_value(self, value)
        if lprev != uprev:
            raise ValueError('can only specify precise prevision')
        return lprev, uprev

    def _validate(self):
        # check that values are non-negative and sum to one
        if any(value[0] != value[1] for value in self.itervalues()):
            raise ValueError("probabilities must be precise")
        if any(value[0] < 0 for value in self.itervalues()):
            raise ValueError("probabilities must be non-negative")
        if sum(value[0] for value in self.itervalues()) != 1:
            raise ValueError("probabilities must sum to one")

    def get_linvac(self, epsilon):
        """Convert probability into a linear vacuous mixture."""
        epsilon = self.number_value(epsilon)
        linvac = LinVac(self.pspace)
        for omega in self.pspace:
            linvac[omega, None] = (1 - epsilon) * self[omega, None][0], None
        return linvac

    def get_lowprev(self, gamble, event=True):
        # faster implementation
        return get_prev(gamble, event)

    def get_prev(self, gamble, event=True):
        """Calculate the conditional expectation."""
        self._validate()
        gamble = Gamble.make(self.pspace, gamble)
        if event is None:
            return sum(self[omega, None][0] * gamble[omega]
                       for omega in self.pspace)
        else:
            event = Event.make(self.pspace, event)
            event_prob = self.get_prev(event.indicator())
            if event_prob == 0:
                raise ZeroDivisionError(
                    "cannot condition on event with zero probability")
            return self.get_prev(gamble * event) / event_prob
