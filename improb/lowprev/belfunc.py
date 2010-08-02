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
    def __init__(self, mass):
        """Construct a belief function from a mass assignment or from
        the mobius inverse of a given lower probability.

        :param mass: The mass assignment.
        :type mass: `improb.SetFunction`
        """
        if not isinstance(mass, improb.setfunction.SetFunction):
            raise TypeError("mass must be SetFunction")
        self._mass = mass

    def __len__(self):
        return len(self._mass)

    def __iter__(self):
        return iter(self._mass)

    def __contains__(self, key):
        return key in self._mass

    def __getitem__(self, key):
        return self._mass[key]

    def __setitem__(self, key, value):
        self._mass[key] = value

    def __delitem__(self, key):
        del self._mass[key]

    def __str__(self):
        return str(self._mass)

    @property
    def pspace(self):
        return self._mass.pspace

    @property
    def mass(self):
        return self._mass

    def set_lower(self, gamble, lprev, event=None):
        raise NotImplementedError('use self[event] = mass')

    def set_upper(self, gamble, lprev, event=None):
        raise NotImplementedError('use self[event] = mass')

    def set_precise(self, gamble, lprev, event=None):
        raise NotImplementedError('use self[event] = mass')

    def get_lower(self, gamble, event=None):
        """Get lower prevision.

        :param gamble: The gamble.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The lower expectation of the gamble.
        :rtype: ``float``

        >>> from improb.lowprev.belfunc import BelFunc
        >>> from improb.lowprev.lowprob import LowProb
        >>> from improb import PSpace
        >>> pspace = PSpace(2)
        >>> lowprob = LowProb(pspace, lprob={(0,): '0.3', (1,): '0.2', (0,1): 1})
        >>> lpr = BelFunc(mass=lowprob.get_mobius_inverse())
        >>> print(lpr.mass)
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

