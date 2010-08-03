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

from improb import PSpace, Gamble, Event
from improb.lowprev.lowpoly import LowPoly

class LowProb(LowPoly):
    """An unconditional lower probability. This class is identical to
    :class:`~improb.lowprev.lowpoly.LowPoly`, except that only
    unconditional assessments on events are allowed.

    >>> print(LowProb(3, lprob={(0, 1): '0.1', (1, 2): '0.2'}))
      0     1     2  
    0.000 1.000 1.000 | 0 1 2 : [0.200,      ]
    1.000 1.000 0.000 | 0 1 2 : [0.100,      ]
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
    """

    # we override _make_key and _make_value to meet the constraints

    def _make_key(self, key):
        gamble, event = LowPoly._make_key(self, key)
        if set(gamble.itervalues()) != set([0, 1]):
            raise ValueError('not an indicator gamble')
        if not event.is_true():
            raise ValueError('not unconditional')
        return gamble, event

    def _make_value(self, value):
        lprev, uprev = LowPoly._make_value(self, value)
        if uprev is not None:
            raise ValueError('cannot specify upper prevision')
        return lprev, uprev

    # TODO also implement __str__
