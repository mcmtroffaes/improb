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

"""Linear vacuous mixtures."""

from __future__ import division, absolute_import, print_function

from improb import PSpace, Gamble, Event
from improb.lowprev.lowprob import LowProb

class LinVac(LowProb):
    """Linear-vacuous mixture, implemented as an unconditional lower
    probability on singletons.

    >>> from improb.lowprev.prob import Prob
    >>> lpr = Prob(3, prob=['0.2', '0.3', '0.5']).get_linvac(epsilon='0.1')
    >>> print lpr.get_lower([1,0,0])
    9/50
    >>> print lpr.get_lower([0,1,0])
    27/100
    >>> print lpr.get_lower([0,0,1])
    9/20
    >>> print lpr.get_lower([3,2,1])
    163/100
    >>> print lpr.get_upper([3,2,1])
    183/100
    >>> lpr = Prob(4, prob=['0.42', '0.08', '0.18', '0.32']).get_linvac(epsilon='0.1')
    >>> print lpr.get_lower([5,5,-5,-5])
    -1/2
    >>> print lpr.get_lower([5,5,-5,-5], set([0,2])) # (6 - 31 * 0.1) / (3 + 2 * 0.1)
    29/32
    >>> print lpr.get_lower([-5,-5,5,5], set([1,3])) # (6 - 31 * 0.1) / (2 + 3 * 0.1) # doctest: +ELLIPSIS
    29/23
    >>> print lpr.get_lower([0,5,0,-5]) # -(6 + 19 * 0.1) / 5
    -79/50
    >>> print lpr.get_lower([0,-5,0,5]) # (6 - 31 * 0.1) / 5
    29/50
    """
    def _make_key(self, key):
        gamble, event = LowProb._make_key(self, key)
        gamble_event = Event.make(self.pspace, gamble)
        if not gamble_event.is_singleton():
            raise ValueError('not a singleton')
        if not event.is_true():
            raise ValueError('must be unconditional')
        return gamble, event

    def get_lower(self, gamble, event=None):
        # this is faster than solving the linear program
        """Get the lower expectation of a gamble conditional on an event.

        :param gamble: The gamble.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The lower expectation of the gamble.
        :rtype: :class:`fractions.Fraction`
        """
        gamble = Gamble.make(self.pspace, gamble)
        event = Event.make(self.pspace, event)
        epsilon = 1 - sum(self[omega, None][0] for omega in self.pspace)
        return (
            (sum(self[omega, None][0] * gamble[omega] for omega in event)
             + epsilon * min(gamble[omega] for omega in event))
            /
            (sum(self[omega, None][0] for omega in event)
             + epsilon)
            )
