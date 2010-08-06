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

from __future__ import division, absolute_import, print_function

from improb import PSpace, Gamble, Event
from improb.lowprev.linvac import LinVac
from improb.lowprev.lowpoly import LowPoly

class Prob(LinVac):
    """A probability measure.

    >>> p = Prob(5, prob=['0.1', '0.2', '0.3', '0.05', '0.35'], number_type='fraction')
    >>> print(p)
    0 : 1/10
    1 : 1/5
    2 : 3/10
    3 : 1/20
    4 : 7/20
    >>> print(p.get_prev([2, 4, 3, 8, 1]))
    53/20
    >>> print(p.get_prev([2, 4, 3, 8, 1], [0, 1]))
    10/3
    """

    def __str__(self):
        return str(
            self.make_gamble(
                [self[{omega: 1}, True][0] for omega in self.pspace]))

    def _make_value(self, value):
        lprev, uprev = LowPoly._make_value(self, value)
        if self.number_cmp(lprev, uprev) != 0:
            raise ValueError('can only specify precise prevision')
        return lprev, uprev

    def is_valid(self, raise_error=False):
        def oops(msg):
            if raise_error:
                raise ValueError(msg)
            else:
                return False
        # check that values are non-negative and sum to one
        if any(self.number_cmp(value[0], value[1]) != 0
               for value in self.itervalues()):
            oops("probabilities must be precise")
        if any(self.number_cmp(value[0], 0) == -1
               for value in self.itervalues()):
            oops("probabilities must be non-negative")
        if self.number_cmp(
            sum(value[0] for value in self.itervalues()), 1) != 0:
            oops("probabilities must sum to one")

    def get_linvac(self, epsilon):
        """Convert probability into a linear vacuous mixture."""
        epsilon = self.make_number(epsilon)
        return LinVac(
            self.pspace,
            lprob=[(1 - epsilon) * self[{omega: 1}, True][0]
                   for omega in self.pspace],
            number_type=self.number_type)

    def get_lowprev(self, gamble, event=True):
        # faster implementation
        return get_prev(gamble, event)

    def get_prev(self, gamble, event=True):
        """Calculate the conditional expectation."""
        self.is_valid(raise_error=True)
        gamble = self.make_gamble(gamble)
        if event is True or (isinstance(event, Event) and event.is_true()):
            # self[{omega: 1}, True][0] is the lower probability ([0])
            # of the indicator gamble of omega ({omega: 1}),
            # unconditionally (True).
            return sum(self[{omega: 1}, True][0] * gamble[omega]
                       for omega in self.pspace)
        else:
            event = self.pspace.make_event(event)
            event_prob = self.get_prev(event.indicator(self.number_type))
            if event_prob == 0:
                raise ZeroDivisionError(
                    "cannot condition on event with zero probability")
            return self.get_prev(gamble * event) / event_prob
