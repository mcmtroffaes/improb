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

"""Coherent lower probabilities."""

from fractions import Fraction
import random

from improb import PSpace, Gamble, Event
from improb.lowprev.lowpoly import LowPoly
from improb.setfunction import SetFunction

class LowProb(LowPoly):
    """An unconditional lower probability. This class is identical to
    :class:`~improb.lowprev.lowpoly.LowPoly`, except that only
    unconditional assessments on events are allowed.

    >>> print(LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2'}))
    0 1   : 0.1
      1 2 : 0.2
    >>> print(LowProb(3, lprev={(3, 1, 0): 1})) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: not an indicator gamble
    >>> print(LowProb(3, uprob={(0, 1): '0.1'})) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: cannot specify upper prevision
    >>> print(LowProb(3, mapping={((3, 1, 0), (0, 1)): ('1.4', None)})) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: not unconditional
    >>> lpr = LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2', (2,): '0.05'}, number_type='fraction')
    >>> lpr.extend()
    >>> print(lpr)
          : 0
    0     : 0
      1   : 0
        2 : 1/20
    0 1   : 1/10
    0   2 : 1/20
      1 2 : 1/5
    0 1 2 : 1
    >>> print(lpr.mobius)
          : 0
    0     : 0
      1   : 0
        2 : 1/20
    0 1   : 1/10
    0   2 : 0
      1 2 : 3/20
    0 1 2 : 7/10
    """

    def _clear_cache(self):
        LowPoly._clear_cache(self)
        try:
            del self._set_function
        except AttributeError:
            pass
        try:
            del self._mobius
        except AttributeError:
            pass

    @property
    def set_function(self):
        """The lower probability as
        :class:`~improb.setfunction.SetFunction`.
        """
        # TODO should return an immutable object

        # implementation detail: this is cached; delete
        # _set_function whenever cache needs to be cleared
        try:
            return self._set_function
        except AttributeError:
            self._set_function = self._make_set_function()
            return self._set_function

    @property
    def mobius(self):
        """The mobius transform of the assigned unconditional lower
        probabilities, as :class:`~improb.setfunction.SetFunction`.

        .. seealso::

            :meth:`improb.setfunction.SetFunction.get_mobius`
                Mobius transform calculation of an arbitrary set function.

            :class:`improb.lowprev.belfunc.BelFunc`
                Belief functions.
        """
        # TODO should return an immutable object

        # implementation detail: this is cached; delete
        # _mobius whenever cache needs to be cleared
        try:
            return self._mobius
        except AttributeError:
            self._mobius = self._make_mobius()
            return self._mobius

    @classmethod
    def make_random(cls, pspace=None, division=None, zero=True, number_type='float'):
        """Generate a random coherent lower probability."""
        # for now this is just a pretty dumb method
        pspace = PSpace.make(pspace)
        lpr = cls(pspace=pspace, number_type=number_type)
        for event in pspace.subsets():
            if len(event) == 0:
                continue
            if len(event) == len(pspace):
                continue
            gamble = event.indicator(number_type)
            if division is None:
                # a number between 0 and len(event) / len(pspace)
                lprob = random.random() * len(event) / len(pspace)
            else:
                # a number between 0 and len(event) / len(pspace)
                # but discretized
                lprob = Fraction(
                    random.randint(
                        0 if zero else 1,
                        (division * len(event)) // len(pspace)),
                    division)
            # make a copy of lpr
            tmplpr = cls(pspace=pspace, mapping=lpr, number_type=number_type)
            # set new assignment, and give up if it incurs sure loss
            tmplpr.set_lower(gamble, lprob)
            if not tmplpr.is_avoiding_sure_loss():
                break
            else:
                lpr.set_lower(gamble, lprob)
        # done! return coherent version of it
        return lpr.get_coherent()

    def __str__(self):
        return str(self.set_function)

    # we override _make_key and _make_value to meet the constraints

    def _make_key(self, key):
        gamble, event = LowPoly._make_key(self, key)
        if not event.is_true():
            raise ValueError('not unconditional')
        return gamble, event

    def _make_value(self, value):
        lprev, uprev = LowPoly._make_value(self, value)
        if uprev is not None:
            raise ValueError('cannot specify upper prevision')
        return lprev, uprev

    def _make_set_function(self):
        return SetFunction(
            self.pspace,
            dict((self.pspace.make_event(gamble), lprev)
                 for (gamble, cond_event), (lprev, uprev) in self.iteritems()),
            self.number_type)

    def _make_mobius(self):
        """Constructs basic belief assignment corresponding to the
        assigned unconditional lower probabilities.
        """
        # construct set function corresponding to this lower probability
        return SetFunction(
            self.pspace,
            dict((event, self.set_function.get_mobius(event))
                 for event in self.pspace.subsets()),
            self.number_type)

    def extend(self, keys=None, lower=True, upper=True):
        if keys is None:
            LowPoly.extend(
                self,
                ((event, True) for event in self.pspace.subsets()),
                lower=True,
                upper=False)
        else:
            LowPoly.extend(self, keys, lower, upper)
