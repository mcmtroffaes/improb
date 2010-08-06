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

"""Lower previsions."""

from __future__ import division, absolute_import, print_function

from abc import ABCMeta, abstractproperty, abstractmethod
from cdd import NumberTypeable
import collections
from fractions import Fraction
import itertools

from improb import PSpace, Gamble, Event
from improb.setfunction import SetFunction

class LowPrev(collections.MutableMapping, NumberTypeable):
    """Abstract base class for working with arbitrary lower previsions."""
    __metaclass__ = ABCMeta

    @abstractproperty
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        raise NotImplementedError

    @abstractmethod
    def get_lower(self, gamble, event=True):
        """Return the lower expectation for *gamble* conditional on
        *event* via natural extension.

        :param gamble: The gamble whose upper expectation to find.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The upper bound for this expectation, i.e. the natural extension of the gamble.
        :rtype: :class:`fractions.Fraction`
        :raises: :exc:`~exceptions.ValueError` if it incurs sure loss
        """
        raise NotImplementedError

    def make_gamble(self, gamble):
        """If *gamble* is

        * a :class:`Gamble`, then checks possibility space and number
          type and returns *gamble*,

        * an :class:`Event`, then checks possibility space and returns
          the indicator of *gamble* with the correct number type,

        * anything else, then construct a :class:`Gamble` using
          *gamble* as data.

        :param gamble: The gamble.
        :type gamble: |gambletype|
        :return: A gamble.
        :rtype: :class:`Gamble`
        :raises: :exc:`~exceptions.ValueError` if possibility spaces
            or number types do not match

        >>> from improb import PSpace, Event, Gamble
        >>> from improb.lowprev.lowpoly import LowPoly
        >>> lpr = LowPoly(pspace='abc', number_type='fraction')
        >>> event = Event('abc', 'ac')
        >>> gamble = event.indicator('fraction')
        >>> fgamble = event.indicator('float')
        >>> pevent = Event('ab', False)
        >>> pgamble = Gamble('ab', [2, 5], number_type='fraction')
        >>> print(lpr.make_gamble({'b': 1}))
        a : 0
        b : 1
        c : 0
        >>> print(lpr.make_gamble(event))
        a : 1
        b : 0
        c : 1
        >>> print(lpr.make_gamble(gamble))
        a : 1
        b : 0
        c : 1
        >>> print(lpr.make_gamble(fgamble)) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> print(lpr.make_gamble(pevent)) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> print(lpr.make_gamble(pgamble)) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> print(lpr.make_gamble({'a': 1, 'b': 0, 'c': 8}))
        a : 1
        b : 0
        c : 8
        >>> print(lpr.make_gamble(range(2, 9, 3)))
        a : 2
        b : 5
        c : 8
        """
        if isinstance(gamble, Gamble):
            if self.pspace != gamble.pspace:
                raise ValueError('possibility space mismatch')
            if self.number_type != gamble.number_type:
                raise ValueError('number type mismatch')
            return gamble
        elif isinstance(gamble, Event):
            if self.pspace != gamble.pspace:
                raise ValueError('possibility space mismatch')
            return gamble.indicator(self.number_type)
        else:
            return Gamble(self.pspace, gamble, self.number_type)

    def get_upper(self, gamble, event=True):
        """Return the upper expectation for *gamble* conditional on
        *event* via natural extension.

        :param gamble: The gamble whose upper expectation to find.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :return: The upper bound for this expectation, i.e. the natural extension of the gamble.
        :rtype: :class:`fractions.Fraction`
        :raises: :exc:`~exceptions.ValueError` if it incurs sure loss
        """
        gamble = self.make_gamble(gamble)
        return -self.get_lower(gamble=-gamble, event=event)

    #def getcredalset(self):
    #    """Find credal set corresponding to this lower prevision."""
    #    raise NotImplementedError

    def is_avoiding_sure_loss(self):
        """No Dutch book? Does the lower prevision avoid sure loss?

        :return: :const:`True` if avoids sure loss, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        try:
            self.get_lower([0] * len(self.pspace))
        except ValueError:
            return False
        return True

    def is_coherent(self):
        """Do all assessments coincide with their natural extension? Is the
        lower prevision coherent?

        :return: :const:`True` if coherent, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss():
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, event in self:
            lprev, uprev = self[gamble, event]
            if (lprev is not None
                and self.number_cmp(
                    self.get_lower(gamble, event), lprev) == 1):
                return False
            if (uprev is not None
                and self.number_cmp(
                    self.get_upper(gamble, event), uprev) == -1):
                return False
        return True

    def is_linear(self):
        """Is the lower prevision a linear prevision? More precisely,
        we check that the natural extension is linear on the linear
        span of the domain of the lower prevision.

        :return: :const:`True` if linear, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        # first check if we are avoiding sure loss
        if not self.is_avoiding_sure_loss():
            return False
        # we're avoiding sure loss, so check the natural extension
        for gamble, event in self:
            if self.number_cmp(
                self.get_lower(gamble, event),
                self.get_upper(gamble, event)) != 0:
                return False
        return True

    def dominates(self, gamble, other_gamble, event=True):
        """Does *gamble* dominate *other_gamble* in lower prevision?

        :return: :const:`True` if *gamble* dominates *other_gamble*, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        gamble = self.make_gamble(gamble)
        other_gamble = self.make_gamble(other_gamble)
        return self.number_cmp(
            self.get_lower(gamble - other_gamble, event), 0) == 1
