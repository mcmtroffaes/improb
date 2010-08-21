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
from improb.lowprev import LowPrev

class Opt:
    """Abstract base class for optimality operators."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, gambles, event=True):
        """Yields optimal gambles from the given set of gambles."""
        raise NotImplementedError

class OptPartialPreorder(Opt):
    """Abstract base class for optimality operators that use a
    maximality criterion with respect to a partial preordering.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_strictly_larger(self, gamble, other_gamble, event=True):
        """Defines the partial ordering."""
        raise NotImplementedError

    def __call__(self, gambles, event=True):
        """Yields optimal gambles from the given set of gambles."""
        # keep track of maximal gambles
        maximal_gambles = []
        # make a stack of all possibly maximal gambles
        # (this also makes a copy so we don't modify the original)
        gambles = list(gambles)
        while gambles:
            # pop a candidate maximal gamble from the stack
            gamble = gambles.pop(0)
            # compare gamble against other maximal gambles
            for other_gamble in maximal_gambles:
                if self.is_strictly_larger(other_gamble, gamble, event):
                    # not maximal
                    break
            else:
                # compare gamble against remaining possibly maximal gambles
                for other_gamble in gambles:
                    if self.is_strictly_larger(other_gamble, gamble, event):
                        # not maximal
                        break
                else:
                    # we found a maximal one!
                    yield gamble
                    maximal_gambles.append(gamble)

class OptTotalPreorder(Opt, cdd.NumberTypeable):
    """Abstract base class for optimality operators that use a
    maximality criterion with respect to a total preordering, which is
    assumed to be represented via real numbers.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_value(self, gamble, event=True):
        """Defines the total order.

        :return: The value of the gamble.
        :rtype: |numbertype|
        """
        raise NotImplementedError

    def __call__(self, gambles, event=True):
        """Yields optimal gambles from the given set of gambles."""
        # keep track of currently maximal gambles and value
        maximal_gambles = []
        maximal_value = None
        for gamble in gambles:
            # compare gamble against currently maximal gambles
            value = self.get_value(gamble, event)
            diff = (self.number_cmp(maximal_value, value)
                    if maximal_gambles else -1)
            if diff < 0:
                # found a better one!
                maximal_gambles = [gamble]
                maximal_value = value
            elif diff == 0:
                # gamble is equally good, so also register it
                maximal_gambles.append(gamble)
        # return result
        for gamble in maximal_gambles:
            yield gamble

class OptAdmissible(OptPartialPreorder, cdd.NumberTypeable):
    """Optimality by pointwise dominance."""
    def __init__(self, pspace, number_type=None):
        if number_type is None:
            number_type = 'float'
        cdd.NumberTypeable.__init__(self, number_type)
        self._pspace = PSpace.make(pspace)

    @property
    def pspace(self):
        return self._pspace

    def is_strictly_larger(self, gamble, other_gamble, event=True):
        """Check for pointwise dominance.

        >>> opt = OptAdmissible('abc', number_type='fraction')
        >>> opt.is_strictly_larger([1, 2, 3], [1, 2, 3])
        False
        >>> opt.is_strictly_larger([1, 2, 3], [1, 1, 4])
        False
        >>> opt.is_strictly_larger([1, 2, 3], [0, 1, 2])
        True
        >>> opt.is_strictly_larger([1, 2, 3], [2, 3, 4])
        False
        >>> opt.is_strictly_larger([1, 2, 3], [1, 2, '8/3'])
        True
        >>> opt.is_strictly_larger([1, 2, 3], [1, 5, 2], event='ac')
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

class OptLowPrevMax(OptPartialPreorder):
    """Maximality with respect to a lower prevision."""
    def __init__(self, lowprev):
        if not isinstance(lowprev, LowPrev):
            raise TypeError("expected a lower prevision as first argument")
        self._lowprev = lowprev

    def is_strictly_larger(self, gamble, other_gamble, event=True):
        return self._lowprev.dominates(gamble, other_gamble, event=event)

class OptLowPrevMaxMin(OptTotalPreorder):
    """Gamma-maximin with respect to a lower prevision."""
    def __init__(self, lowprev):
        if not isinstance(lowprev, LowPrev):
            raise TypeError("expected a lower prevision as first argument")
        cdd.NumberTypeable.__init__(self, lowprev.number_type)
        self._lowprev = lowprev

    def get_value(self, gamble, event=True):
        return self._lowprev.get_lower(gamble, event=event)

class OptLowPrevMaxMax(OptLowPrevMaxMin):
    """Gamma-maximax with respect to a lower prevision."""

    def get_value(self, gamble, event=True):
        return self._lowprev.get_upper(gamble, event=event)

class OptLowPrevMaxHurwicz(OptLowPrevMaxMin):
    """Hurwicz with respect to a lower prevision."""
    def __init__(self, lowprev, alpha):
        OptLowPrevMaxMin.__init__(self, lowprev)
        self.alpha = self.make_number(alpha)

    def get_value(self, gamble, event=True):
        return (self.alpha * self._lowprev.get_upper(gamble, event=event)
                + (1 - self.alpha) * self._lowprev.get_lower(gamble, event=event))

class OptLowPrevMaxInterval(OptLowPrevMax):
    """Interval dominance with respect to a lower prevision."""

    # TODO implement faster algorithm
    def is_strictly_larger(self, gamble, other_gamble, event=True):
        return self._lowprev.number_cmp(
            self._lowprev.get_lower(gamble, event=event),
            self._lowprev.get_upper(other_gamble, event=event)) > 0
