# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2011, Matthias Troffaes
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
import cdd
import collections
from fractions import Fraction
import itertools

from improb import PSpace, Gamble, Event
from improb.setfunction import SetFunction

class LowPrev(cdd.NumberTypeable):
    """Abstract base class for working with arbitrary lower previsions.

    A lower prevision is understood to be an intersection of
    half-spaces, each of which constrains the set of probability mass
    functions.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        raise NotImplementedError

    def get_lower(self, gamble, event=True, algorithm=None):
        """Return the lower expectation---or an approximation
        thereof---for *gamble* conditional on *event* via the
        prescribed *algorithm*.

        :param gamble: The gamble whose upper expectation to find.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :param algorithm: The algorithm to use. The default value,
            ``None``, returns ``self[gamble, event]``.
        :type algorithm: :class:`str`
        :return: The lower bound for the conditional expectation.
        :rtype: :class:`float` or :class:`~fractions.Fraction`
        """
        if algorithm is None:
            return self._get_lower(gamble, event)
        elif algorithm == "natext":
            return self.get_lower_natext(gamble, event)
        elif algorithm == "choquet":
            return self.get_lower_choquet(gamble, event)
        elif algorithm == "linvac":
            return self.get_lower_linvac(gamble, event)
        else:
            raise ValueError("unknown algorithm '{0}'".format(algorithm))

    def get_upper(self, gamble, event=True, algorithm=None):
        """Return the upper expectation---or an approximation
        thereof---for *gamble* conditional on *event* via the
        prescribed *algorithm*.

        :param gamble: The gamble whose upper expectation to find.
        :type gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :param algorithm: The algorithm to use. The default value,
            ``None``, returns ``-self[-gamble, event]``.
        :type algorithm: :class:`str`
        :return: The upper bound for the conditional expectation.
        :rtype: :class:`float` or :class:`~fractions.Fraction`
        """
        gamble = self.make_gamble(gamble)
        return -self.get_lower(gamble=-gamble, event=event, algorithm=algorithm)

    @abstractmethod
    def _get_lower(self, gamble, event):
        raise NotImplementedError

    @abstractmethod
    def get_lower_natext(self, gamble, event=True):
        raise NotImplementedError

    def get_lower_choquet(self, gamble, event=True):
        """Approximate lower expectation by Choquet integration."""
        result = 0
        gamble = self.make_gamble(gamble)
        event = self.make_event(event)
        # find values and level sets of the gamble
        gamble_inverse = collections.defaultdict(set)
        for key in event:
            gamble_inverse[gamble[key]].add(key)
        items = sorted(gamble_inverse.iteritems())
        # now calculate the Choquet integral
        subevent = set(event) # use set as it must be mutable
        previous_value = 0
        for value, keys in items:
            result += (
                (value - previous_value)
                * self.get_lower(self.make_event(subevent), event))
            previous_value = value
            subevent -= keys
        return result

    def get_lower_linvac(self, gamble, event=True):
        """Approximate lower expectation by linear vacuous mixture."""
        gamble = self.make_gamble(gamble)
        event = self.pspace.make_event(event)
        lowprob = dict((omega, self.get_lower({omega: 1}, True))
                       for omega in self.pspace)
        epsilon = 1 - sum(lowprob.itervalues())
        return (
            (sum(lowprob[omega] * gamble[omega] for omega in event)
             + epsilon * min(gamble[omega] for omega in event))
            /
            (sum(lowprob[omega] for omega in event)
             + epsilon)
            )

    def make_gamble(self, gamble):
        return self.pspace.make_gamble(gamble, self.number_type)

    @abstractmethod
    def is_avoiding_sure_loss(self, algorithm=None):
        """No Dutch book? Does the lower prevision avoid sure loss?

        :return: :const:`True` if avoids sure loss, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        raise NotImplementedError

    @abstractmethod
    def is_coherent(self, algorithm=None):
        """Do all assessments coincide with their natural extension? Is the
        lower prevision coherent?

        :param algorithm: The algorithm to use (the default value uses
           the most efficient algorithm).
        :type algorithm: :class:`str`
        :return: :const:`True` if coherent, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        raise NotImplementedError

    @abstractmethod
    def is_linear(self, algorithm=None):
        """Is the lower prevision a linear prevision? More precisely,
        we check that the natural extension is linear on the linear
        span of the domain of the lower prevision.

        :param algorithm: The algorithm to use (the default value uses
           the most efficient algorithm).
        :type algorithm: :class:`str`
        :return: :const:`True` if linear, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        raise NotImplementedError

    def dominates(self, gamble, other_gamble, event=True, algorithm=None):
        """Does *gamble* dominate *other_gamble* in lower prevision?

        :param gamble: The left hand side gamble.
        :type gamble: |gambletype|
        :param other_gamble: The right hand side gamble.
        :type other_gamble: |gambletype|
        :param event: The event to condition on.
        :type event: |eventtype|
        :param algorithm: The algorithm to use (the default value uses
           the most efficient algorithm).
        :type algorithm: :class:`str`
        :return: :const:`True` if *gamble* dominates *other_gamble*, :const:`False` otherwise.
        :rtype: :class:`bool`
        """
        gamble = self.make_gamble(gamble)
        other_gamble = self.make_gamble(other_gamble)
        return self.number_cmp(
            self.get_lower(gamble - other_gamble, event, algorithm)) == 1

    @abstractmethod
    def get_extend_domain(self):
        """Get largest possible domain to which the lower prevision
        can be extended.
        """
        raise NotImplementedError
