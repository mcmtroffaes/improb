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

"""A module for working with probability measures."""

from __future__ import division, absolute_import, print_function

import math
import random
import fractions

from improb import PSpace, Gamble, Event, _str_keys_values
from improb.lowprev.linvac import LinVac
from improb.lowprev.lowpoly import LowPoly

class Prob(LinVac):
    """A probability measure, implemented as a
    :class:`~improb.lowprev.linvac.LinVac` whose natural extension is
    calculated via expectation; see :meth:`get_precise`.

    >>> p = Prob(5, prob=['0.1', '0.2', '0.3', '0.05', '0.35'])
    >>> print(p)
    0 : 1/10
    1 : 1/5
    2 : 3/10
    3 : 1/20
    4 : 7/20
    >>> print(p.get_precise([2, 4, 3, 8, 1]))
    53/20
    >>> print(p.get_precise([2, 4, 3, 8, 1], [0, 1]))
    10/3

    >>> p = Prob(3, prob={(0,): '0.4'})
    >>> print(p)
    0 : 2/5
    1 : undefined
    2 : undefined
    >>> p.extend()
    >>> print(p)
    0 : 2/5
    1 : 3/10
    2 : 3/10
    """

    def __str__(self):
        return _str_keys_values(
            self.pspace,
            (self.get(({omega: 1}, True), ("undefined", "undefined"))[0]
             for omega in self.pspace))

    def _make_value(self, value):
        lprev, uprev = LowPoly._make_value(self, value)
        if self.number_cmp(lprev, uprev) != 0:
            raise ValueError('can only specify precise prevision')
        return lprev, uprev

    def is_valid(self, raise_error=False):
        def oops(msg):
            if raise_error:
                raise ValueError(msg)
            else:
                return False
        # check that values are non-negative and sum to one
        if any(self.number_cmp(value[0], value[1]) != 0
               for value in self.itervalues()):
            return oops("probabilities must be precise")
        if any(self.number_cmp(value[0], 0) == -1
               for value in self.itervalues()):
            return oops("probabilities must be non-negative")
        if self.number_cmp(
            sum(value[0] for value in self.itervalues()), 1) != 0:
            return oops("probabilities must sum to one")
        return True

    def get_linvac(self, epsilon):
        """Convert probability into a linear vacuous mixture:

        .. math::

           \underline{E}(f)=(1-\epsilon)E(f)+\epsilon\inf f"""
        epsilon = self.make_number(epsilon)
        return LinVac(
            self.pspace,
            lprob=[(1 - epsilon) * self[{omega: 1}, True][0]
                   for omega in self.pspace],
            number_type=self.number_type)

    def get_lowprev(self, gamble, event=True, algorithm='linear'):
        # faster implementation
        return get_precise(gamble, event, algorithm)

    def get_precise(self, gamble, event=True, algorithm='linear'):
        r"""Calculate the conditional expectation,

        .. math::

           E(f|A)=
           \frac{
           \sum_{\omega\in A}p(\omega)f(\omega)
           }{
           \sum_{\omega\in A}p(\omega)
           }

        where :math:`p(\omega)` is simply the probability of the
        singleton :math:`\omega`::

            self[{omega: 1}, True][0]
        """
        # default algorithm
        if algorithm is None:
            algorithm = 'linear'
        # other algorithms?
        if algorithm != 'linear':
            return LinVac.get_lower(self, gamble, event, algorithm)
        self.is_valid(raise_error=True)
        gamble = self.make_gamble(gamble)
        if event is True or (isinstance(event, Event) and event.is_true()):
            # self[{omega: 1}, True][0] is the lower probability ([0])
            # of the indicator gamble of omega ({omega: 1}),
            # unconditionally (True).
            return sum(self[{omega: 1}, True][0] * gamble[omega]
                       for omega in self.pspace)
        else:
            event = self.pspace.make_event(event)
            event_prob = self.get_precise(event.indicator(self.number_type))
            if event_prob == 0:
                raise ZeroDivisionError(
                    "cannot condition on event with zero probability")
            return self.get_precise(gamble * event) / event_prob

    @classmethod
    def make_random(cls, pspace=None, division=None, zero=True,
                    number_type='float'):
        """Generate a random probability mass function.

        >>> import random
        >>> random.seed(25)
        >>> print(Prob.make_random("abcd", division=10))
        a : 0.4
        b : 0.0
        c : 0.1
        d : 0.5
        >>> random.seed(25)
        >>> print(Prob.make_random("abcd", division=10, zero=False))
        a : 0.3
        b : 0.1
        c : 0.2
        d : 0.4
        """
        pspace = PSpace.make(pspace)
        lpr = cls(pspace=pspace, number_type=number_type)
        # get a uniform sample from the simplex
        probs = [-math.log(random.random()) for omega in pspace]
        sum_probs = sum(probs)
        probs = [prob / sum_probs for prob in probs]
        if division is not None:
            # discretize the probabilities
            probs = [int(prob * division + 0.5) + (0 if zero else 1)
                     for prob in probs]
            # now, again ensure they sum to division
            while sum(probs) < division:
                probs[random.randrange(len(probs))] += 1
            while sum(probs) > division:
                while True:
                    idx = random.randrange(len(probs))
                    if probs[idx] > (1 if zero else 2):
                        probs[idx] -= 1
                        break
            # convert to fraction
            probs = [fractions.Fraction(prob, division) for prob in probs]
        # return the probability
        return cls(pspace=pspace, number_type=number_type, prob=probs)

    # probs have an upper, so default to upper=True
    def extend(self, keys=None, lower=True, upper=True, algorithm='linear'):
        # default algorithm
        if algorithm is None:
            algorithm = 'linear'
        # other algorithms?
        if algorithm != 'linear':
            LinVac.extend(self, keys, lower, upper, algorithm)
            return
        # number of undefined singletons?
        num_undefined = len(self.pspace) - len(self)
        if num_undefined == 0:
            # nothing to do
            return
        # sum probabilities over all defined singletons
        mass = sum(self.get(({omega: 1}, True), (0, 0))[0]
                   for omega in self.pspace)
        # distribute remaining probability over remaining events
        remaining_mass = (1 - mass) / num_undefined
        value = (remaining_mass, remaining_mass)
        for omega in self.pspace:
            key = ({omega: 1}, True)
            if key not in self:
                self[key] = value
