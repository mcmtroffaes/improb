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
from improb.lowprev import LowPrev

class LinVac(LowPrev):
    """Linear-vacuous mixture.

    >>> from improb.lowprev import LinVac
    >>> lpr = LinVac([0.2, 0.4, 0.5], 0.1) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: probabilities must sum to one

    >>> from improb.lowprev import LinVac
    >>> lpr = LinVac([0.2, 0.3, 0.5], 0.1)
    >>> print lpr.get_lower([1,0,0])
    0.18
    >>> print lpr.get_lower([0,1,0])
    0.27
    >>> print lpr.get_lower([0,0,1])
    0.45
    >>> print lpr.get_lower([3,2,1])
    1.63
    >>> print lpr.get_upper([3,2,1])
    1.83

    >>> from improb.lowprev import LinVac
    >>> lpr = LinVac([0.42, 0.08, 0.18, 0.32], 0.1)
    >>> print lpr.get_lower([5,5,-5,-5])
    -0.5
    >>> print lpr.get_lower([5,5,-5,-5], set([0,2])) # (6 - 31 * 0.1) / (3 + 2 * 0.1)
    0.90625
    >>> print lpr.get_lower([-5,-5,5,5], set([1,3])) # (6 - 31 * 0.1) / (2 + 3 * 0.1) # doctest: +ELLIPSIS
    1.260869...
    >>> print lpr.get_lower([0,5,0,-5]) # -(6 + 19 * 0.1) / 5
    -1.58
    >>> print lpr.get_lower([0,-5,0,5]) # (6 - 31 * 0.1) / 5
    0.58
    """
    def __init__(self, prob, epsilon):
        if isinstance(prob, (list, tuple)):
            tot = sum(prob)
            self._pspace = tuple(xrange(len(prob)))
        elif isinstance(prob, dict):
            tot = sum(prob.itervalues())
            self._pspace = tuple(w for w in prob)
        if tot < 1 - 1e-6 or tot > 1 + 1e-6:
            raise ValueError("probabilities must sum to one")
        self._prob = prob
        self._epsilon = epsilon
        self._matrix = None

    def __iter__(self):
        raise NotImplementedError

    def set_lower(self, gamble, event=None):
        raise NotImplementedError

    def set_upper(self, gamble, event=None):
        raise NotImplementedError
    
    def set_precise(self, gamble, event=None):
        raise NotImplementedError

    def get_lower(self, gamble, event=None):
        """Get the lower expectation of a gamble conditional on an event.

        :param gamble: The gamble.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The lower expectation of the gamble.
        :rtype: ``float``
        """
        gamble = Gamble.make(self.pspace, gamble)
        if event is None:
            event = set(self.pspace)
        return (
            ((1 - self._epsilon) * sum(self._prob[w] * gamble[w] for w in event)
             + self._epsilon * min(gamble[w] for w in event))
            /
            ((1 - self._epsilon) * sum(self._prob[w] for w in event)
             + self._epsilon)
            )

