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

import collections
from fractions import Fraction

from improb import PSpace, Gamble, Event, _fraction, _fraction_repr
from improb.lowprev.lowprob import LowProb

class Prob(LowProb):
    """A probability measure.

    >>> p = Prob(5, ['0.1', '0.2', '0.3', '0.05', '0.35'])
    >>> print(p)
    0 : 0.100
    1 : 0.200
    2 : 0.300
    3 : 0.050
    4 : 0.350
    >>> print(p.get_prev([2, 4, 3, 8, 1]))
    53/20
    >>> print(p.get_prev([2, 4, 3, 8, 1], [0, 1]))
    10/3
    """

    def __init__(self, pspace, mapping=None):
        """Construct a probability measure on the given possibility space.

        :param pspace: The possibility space.
        :type pspace: |pspacetype|
        :param mapping: A mapping that defines the probability of each atom.
        :type mapping: :class:`dict`
        """

        self._pspace = PSpace.make(pspace)
        if mapping is not None:
            self._prob = dict((omega, _fraction(mapping[omega]))
                              for omega in self.pspace)
        else:
            self._prob = dict((omega, Fraction(1, len(self.pspace)))
                              for omega in self.pspace)
        self._validate()

    def _validate(self):
        # check that values are non-negative and sum to one
        if any(value < 0 for value in self._prob.itervalues()):
            raise ValueError("probabilities must be non-negative")
        if sum(self._prob.itervalues()) != 1:
            raise ValueError("probabilities must sum to one")

    def update(self, mapping):
        """Update the probabilities using the given mapping.

        :param mapping: A mapping that defines the probability of each atom.
        :type mapping: :class:`dict`
        """
        oldprob = self._prob.copy()
        self._prob = dict((omega, _fraction(mapping[omega]))
                          for omega in self.pspace)
        try:
            self._validate()
        except ValueError:
            self._prob = oldprob
            raise

    def __len__(self):
        return len(self._prob)

    def __iter__(self):
        # not iter(self._prob) because we wish to iterate in same
        # order as self.pspace
        return (self._prob[omega] for omega in self.pspace)

    def __contains__(self, gamble):
        return self.pspace.make_element(gamble) in self._prob

    def __getitem__(self, gamble):
        return self._prob[self.pspace.make_element(gamble)]

    def __setitem__(self, gamble):
        raise NotImplementedError("use the update() method instead")

    def __str__(self):
        return str(Gamble(self.pspace, self))

    def get_lowprev(self, gamble, event=None):
        return get_prev(gamble, event)

    def get_prev(self, gamble, event=None):
        """Calculate the conditional expectation."""
        gamble = Gamble.make(self.pspace, gamble)
        if event is None:
            return sum(self[omega] * gamble[omega] for omega in self.pspace)
        else:
            event = Event.make(self.pspace, event)
            event_prob = self.get_prev(event.indicator())
            if event_prob == 0:
                raise ZeroDivisionError(
                    "cannot condition on event with zero probability")
            return self.get_prev(gamble * event) / event_prob

    @property
    def pspace(self):
        """An :class:`~improb.PSpace` representing the possibility space."""
        return self._pspace
