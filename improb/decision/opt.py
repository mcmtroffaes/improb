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

"""Optimality operators."""

from __future__ import division, absolute_import, print_function

from abc import ABCMeta, abstractproperty, abstractmethod
import cdd

from improb import PSpace, Gamble, Event
from improb.decision import filter_maximal
from improb.lowprev import LowPrev

class Opt:
    def __call__(self, gambles, event=True):
        """Yields optimal gambles from the given set of gambles."""
        raise NotImplementedError

class OptAdmissible(Opt, cdd.NumberTypeable):
    """Optimality by pointwise dominance."""
    def __init__(self, pspace, number_type=None):
        self._pspace = PSpace.make(pspace)

    @property
    def pspace(self):
        return self._pspace

    def dominates(self, gamble, other_gamble, event=True):
        """Check for pointwise dominance.

        >>> opt = OptAdmissible('abc', number_type='fraction')
        >>> opt.dominates([1, 2, 3], [1, 2, 3])
        False
        >>> opt.dominates([1, 2, 3], [1, 1, 4])
        False
        >>> opt.dominates([1, 2, 3], [0, 1, 2])
        True
        >>> opt.dominates([1, 2, 3], [2, 3, 4])
        False
        >>> opt.dominates([1, 2, 3], [1, 2, '8/3'])
        True
        >>> opt.dominates([1, 2, 3], [1, 5, 2], event='ac')
        True
        """
        gamble = self.pspace.make_gamble(gamble, self.number_type)
        other_gamble = self.pspace.make_gamble(other_gamble, self.number_type)
        event = self.pspace.make_event(event)
        diffs = set(
            self.number_cmp(gamble[omega], other_gamble[omega])
            for omega in event)
        return (all(diff >= 0 for diff in diffs)
                and
                any(diff > 0 for diff in diffs))
    

class OptLowPrevMax(Opt):
    """Maximality with respect to a lower prevision."""
    def __init__(self, lowprev):
        if not isinstance(lowprev, LowPrev):
            raise TypeError("expected a lower prevision as first argument")
        self._lowprev = lowprev

    def __call__(self, gambles, event=True):
        return filter_maximal(gambles, self._lowprev.dominates, event)
