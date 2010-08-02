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

"""Belief functions."""

from __future__ import division, absolute_import, print_function

from improb import PSpace, Gamble, Event
from improb.lowprev import LowPrev

class BelFunc(LowPrev):
    def __init__(self, mass=None, lowprob=None):
        """Construct a belief function from a mass assignment or from
        the mobius inverse of a given lower probability.

        :param mass: The mass assignment.
        :type mass: `improb.SetFunction`
        :param lowprob: The lower probability.
        :type lowprob: `improb.SetFunction`
        """
        self._mass = {}
        if mass:
            self._mass = mass
        elif lowprob:
            self._mass = lowprob.get_mobius_inverse()
        else:
            raise ValueError("must specify mass or lowprob")
        self._pspace = self._mass._pspace

    @property
    def mass(self):
        return self._mass

    def get_lower(self, gamble, event=None):
        """Get lower prevision.

        :param gamble: The gamble.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The lower expectation of the gamble.
        :rtype: ``float``

        >>> from improb.lowprev import BelFunc
        >>> from improb import PSpace, SetFunction
        >>> pspace = PSpace(2)
        >>> lowprob = SetFunction(pspace, {(0,): '0.3', (1,): '0.2', (0,1): 1})
        >>> lpr = BelFunc(lowprob=lowprob)
        >>> print(lpr.mass)
            : 0.000
        0   : 0.300
          1 : 0.200
        0 1 : 0.500
        >>> print(lpr.get_lower([1,0]))
        3/10
        >>> print(lpr.get_lower([0,1]))
        1/5
        >>> print(lpr.get_lower([4,9])) # 0.8 * 4 + 0.2 * 9
        5
        >>> print(lpr.get_lower([5,1])) # 0.3 * 5 + 0.7 * 1
        11/5
        """
        gamble = Gamble.make(self.pspace, gamble)
        if event is not None:
            raise NotImplementedError
        return sum(
            (self._mass[event_] * min(gamble[w] for w in event_)
             for event_ in self.pspace.subsets()
             if event_),
            0)

