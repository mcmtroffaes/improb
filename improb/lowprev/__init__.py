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
import collections
from fractions import Fraction
import itertools

from improb import PSpace, Gamble, Event
from improb.setfunction import SetFunction

class LowPrev(collections.Mapping):
    """Abstract base class for working with arbitrary lower previsions."""
    __metaclass__ = ABCMeta

    def _make_key(self, key):
        """Helper function to construct a key, that is, a gamble/event pair."""
        gamble, event = key
        return Gamble.make(self.pspace, gamble), Event.make(self.pspace, event)

    def _make_value(self, value):
        """Helper function to construct a value, that is, a
        lower/upper prevision pair.
        """
        lprev, uprev = value
        return (
            _fraction(lprev) if lprev is not None else None,
            _fraction(uprev) if uprev is not None else None)

    @abstractproperty
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        raise NotImplementedError

    @abstractmethod
    def get_lower(self, gamble, event=None):
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

    def get_upper(self, gamble, event=None):
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
        gamble, event = self._make_key((gamble, event))
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
            self.get_lower(dict((w, 0) for w in self.pspace))
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
            if lprev is not None and self.get_lower(gamble, event) > lprev:
                return False
            if uprev is not None and self.get_upper(gamble, event) < uprev:
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
            if self.get_lower(gamble, event) != self.get_upper(gamble, event):
                return False
        return True

    def dominates(self, gamble, other_gamble, event=None):
        """Does *gamble* dominate *other_gamble* in lower prevision?

        :return: :const:`True` if *gamble* dominates *other_gamble*, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        gamble = Gamble.make(self.pspace, gamble)
        other_gamble = Gamble.make(self.pspace, other_gamble)
        return self.get_lower(gamble - other_gamble, event) > 0

    def get_lowprob(self):
        """Return lower probability (i.e. restriction of natural
        extension to indicators).

        :return: The lower probability.
        :rtype: :class:`~improb.setfunction.SetFunction`
        """
        return SetFunction(
            self.pspace,
            dict((event, self.get_lower(event))
                 for event in self.pspace.subsets()))

    def get_mobius_inverse(self):
        """Return the mobius inverse of the lower probability determined by
        this lower prevision. This usually only makes sense for completely
        monotone lower previsions.

        :return: The mobius inverse.
        :rtype: :class:`~improb.setfunction.SetFunction`
        """
        return self.get_lowprob().get_mobius_inverse()
