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
from fractions import Fraction

from improb import PSpace, Gamble, Event, _fraction, _fraction_repr
from improb.lowprev.linvac import LinVac

class Prob(LinVac):
    """A probability measure.

    >>> p = Prob(5, ['0.1', '0.2', '0.3', '0.05', '0.35'])
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

    def __init__(self, pspace, mapping=None, prob=None):
        """Construct a probability measure on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param mapping: A mapping that defines the probability of each atom.
        :type mapping: :class:`dict`
        """
        LinVac.__init__(self, pspace, mapping)
        if mapping is None:
            if prob is None:
                for omega in self.pspace:
                    self[omega, None] = Fraction(1, len(pspace)), None
            else:
                for omega in self.pspace:
                    self[omega, None] = prob[omega], None
        self._validate()

    def _validate(self):
        # check that values are non-negative and sum to one
        if any(value[0] < 0 for value in self.itervalues()):
            raise ValueError("probabilities must be non-negative")
        if sum(value[0] for value in self.itervalues()) != 1:
            raise ValueError("probabilities must sum to one")

    def get_linvac(self, epsilon):
        """Convert probability into a linear vacuous mixture."""
        epsilon = _fraction(epsilon)
        linvac = LinVac(self.pspace)
        for omega in self.pspace:
            linvac[omega, None] = (1 - epsilon) * self[omega, None][0], None
        return linvac

    def get_lowprev(self, gamble, event=None):
        # faster implementation
        return get_prev(gamble, event)

    def get_prev(self, gamble, event=None):
        """Calculate the conditional expectation."""
        gamble = Gamble.make(self.pspace, gamble)
        if event is None:
            return sum(self[omega] * gamble[omega] for omega in self.pspace)
        else:
            event = Event.make(self.pspace, event)
            event_prob = self.get_prev(event.indicator())
            if event_prob == 0:
                raise ZeroDivisionError(
                    "cannot condition on event with zero probability")
            return self.get_prev(gamble * event) / event_prob
