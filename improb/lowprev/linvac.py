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
from improb.lowprev.prob import Prob

class LinVac(LowProb):
    """Linear-vacuous mixture.

    >>> lpr = LinVac(prob=[0.2, 0.4, 0.5], epsilon=0.1) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: probabilities must sum to one

    >>> from improb.lowprev import LinVac
    >>> lpr = LinVac(pspace=3, prob=[0.2, 0.3, 0.5], epsilon=0.1)
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
    def __init__(self, pspace=None, prob=None, epsilon=0):
        if isinstance(prob, Prob) and pspace is None:
            self._prob = prob
        else:
            self._prob = Prob.make(PSpace.make(pspace), prob)
        self._epsilon = _fraction(epsilon)

    def __iter__(self):
        raise NotImplementedError

    @property
    def pspace(self):
        return self._prob.pspace

    def set_lower(self, gamble, event=None):
        gamble = Event.make(self.pspace, gamble)
        if len(gamble) != 1:
            raise ValueError('can only set lower bound on singletons')

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

